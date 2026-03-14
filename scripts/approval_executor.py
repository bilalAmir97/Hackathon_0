"""Approval Executor for monitoring and executing approved actions.

This module implements the ApprovalExecutor class that monitors vault folders
for approval workflow state transitions and executes approved actions.
"""

import json
import os
import re
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, UTC

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileMovedEvent

from watchers.gmail_state import create_log_entry, load_config, move_file_atomic
from mcp_servers.email_client import get_email_client


class ApprovalFileHandler(FileSystemEventHandler):
    """File system event handler for approval workflow.

    Monitors Pending_Approval, Approved, and Rejected folders for file movements
    and triggers appropriate actions.
    """

    def __init__(self, executor):
        """Initialize handler with reference to executor.

        Args:
            executor: ApprovalExecutor instance
        """
        self.executor = executor
        super().__init__()

    def on_moved(self, event: FileMovedEvent):
        """Handle file movement events.

        Args:
            event: File moved event from watchdog
        """
        if event.is_directory:
            return

        dest_path = Path(event.dest_path)

        # Check which folder the file was moved to
        if 'Approved' in dest_path.parts:
            self.executor.on_file_moved_to_approved(event.dest_path)
        elif 'Rejected' in dest_path.parts:
            self.executor.on_file_moved_to_rejected(event.dest_path)


class ApprovalExecutor:
    """Monitors vault folders and executes approved actions.

    Uses watchdog to monitor file movements between approval workflow folders.
    Validates approval files, executes approved actions, and logs all transitions.
    """

    def __init__(self, vault_path: str = None):
        """Initialize approval executor.

        Args:
            vault_path: Path to vault directory (default: from config)
        """
        config = load_config()
        self.vault_path = Path(vault_path or config['vault_path'])

        # Folder paths
        self.pending_approval = self.vault_path / 'Pending_Approval'
        self.approved = self.vault_path / 'Approved'
        self.rejected = self.vault_path / 'Rejected'
        self.done = self.vault_path / 'Done'
        self.needs_action = self.vault_path / 'Needs_Action'
        self.logs = self.vault_path / 'Logs'
        self.quarantine = self.vault_path / '.quarantine'

        # Load approval schema
        self.approval_schema = self._load_approval_schema()

        # Failure tracking
        self.consecutive_failures = 0
        self.last_failure_time = None

        # Watchdog observer
        self.observer: Optional[Observer] = None

    def _load_approval_schema(self) -> Dict[str, Any]:
        """Load approval request JSON schema.

        Returns:
            Approval schema dictionary
        """
        schema_path = Path('specs/001-gmail-approval-workflow/contracts/approval-request.schema.json')

        if schema_path.exists():
            with open(schema_path, 'r') as f:
                return json.load(f)

        # Return minimal schema if file doesn't exist
        return {
            "required": ["approval_id", "action_type", "email_action_ref",
                        "action_params", "risk_assessment", "reasoning"]
        }

    def validate_approval_file(self, file_path: str) -> bool:
        """Validate approval file against JSON schema.

        Args:
            file_path: Path to approval file

        Returns:
            True if valid, False otherwise
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract YAML frontmatter
            match = re.search(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
            if not match:
                return False

            frontmatter = match.group(1).strip()

            # Try to parse as JSON
            try:
                data = json.loads(frontmatter)
            except json.JSONDecodeError:
                # Try YAML parsing (simplified - just check for required fields)
                required_fields = self.approval_schema.get('required', [])
                for field in required_fields:
                    if f"{field}:" not in frontmatter:
                        return False
                return True

            # Validate required fields
            required_fields = self.approval_schema.get('required', [])
            for field in required_fields:
                if field not in data:
                    return False

            return True

        except Exception as e:
            print(f"Validation error: {e}")
            return False

    def on_file_moved_to_approved(self, file_path: str):
        """Handle file moved to Approved folder.

        Validates file, executes action, creates log entry, moves to Done.

        Args:
            file_path: Path to approved file
        """
        file_path = Path(file_path)

        print(f"✅ Approved: {file_path.name}")

        # Ensure directories exist
        self.done.mkdir(parents=True, exist_ok=True)
        self.logs.mkdir(parents=True, exist_ok=True)

        # Validate file
        if not self.validate_approval_file(str(file_path)):
            print(f"⚠️ Invalid approval file: {file_path.name}")
            self.handle_corrupted_file(str(file_path))
            return

        # Read approval file to get action details
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                # Extract YAML frontmatter
                if content.startswith('---'):
                    parts = content.split('---', 2)
                    if len(parts) >= 3:
                        approval_data = yaml.safe_load(parts[1])
                    else:
                        raise ValueError("Invalid YAML frontmatter")
                else:
                    raise ValueError("No YAML frontmatter found")
        except Exception as e:
            print(f"❌ Failed to parse approval file: {e}")
            self.handle_corrupted_file(str(file_path))
            return

        # Execute action via MCP
        execution_result = self.execute_action(approval_data)

        # Create log entry for approval
        log_entry = {
            'timestamp': datetime.now(UTC).isoformat() + 'Z',
            'log_id': f"approval_{int(datetime.now(UTC).timestamp())}",
            'action_type': approval_data.get('action_type', 'unknown'),
            'status': execution_result.get('status', 'unknown'),
            'inputs': {
                'approval_file': file_path.name,
                'approval_id': approval_data.get('approval_id', 'unknown')
            },
            'outputs': execution_result
        }
        create_log_entry(str(self.logs), log_entry)

        # Move to Done
        done_file = self.done / file_path.name
        try:
            move_file_atomic(str(file_path), str(done_file))
            print(f"📁 Moved to Done: {file_path.name}")
        except Exception as e:
            print(f"❌ Failed to move to Done: {e}")

    def execute_action(self, approval_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the approved action via MCP.

        Args:
            approval_data: Parsed approval file data

        Returns:
            Dict with execution result (status, message_id, etc.)
        """
        action_type = approval_data.get('action_type', 'unknown')

        print(f"🚀 Executing action: {action_type}")

        if action_type == 'email_send':
            return self.execute_email_send(approval_data)
        else:
            return {
                'status': 'error',
                'error': f'Unknown action type: {action_type}'
            }

    def execute_email_send(self, approval_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute email send action via Email MCP client.

        Args:
            approval_data: Parsed approval file data with action_params

        Returns:
            Dict with execution result
        """
        try:
            action_params = approval_data.get('action_params', {})

            recipient = action_params.get('recipient')
            subject = action_params.get('subject')
            body = action_params.get('body')

            if not all([recipient, subject, body]):
                return {
                    'status': 'error',
                    'error': 'Missing required fields: recipient, subject, or body'
                }

            # Get email client and send
            email_client = get_email_client()
            result = email_client.send_email(
                to=recipient,
                subject=subject,
                body=body,
                cc=action_params.get('cc'),
                bcc=action_params.get('bcc')
            )

            if result.get('status') == 'success':
                print(f"✅ Email sent to {recipient}")
                print(f"   Message ID: {result.get('message_id')}")
            else:
                print(f"❌ Email send failed: {result.get('error')}")

            return result

        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }

    def on_file_moved_to_rejected(self, file_path: str):
        """Handle file moved to Rejected folder.

        Skips execution, creates log entry, moves to Done.

        Args:
            file_path: Path to rejected file
        """
        file_path = Path(file_path)

        print(f"❌ Rejected: {file_path.name}")

        # Ensure directories exist
        self.done.mkdir(parents=True, exist_ok=True)
        self.logs.mkdir(parents=True, exist_ok=True)

        # Create log entry for rejection
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'log_id': f"rejection_{int(datetime.utcnow().timestamp())}",
            'action_type': 'approval_rejected',
            'status': 'success',
            'inputs': {'approval_file': file_path.name}
        }
        create_log_entry(str(self.logs), log_entry)

        # Move to Done (without execution)
        done_file = self.done / file_path.name
        try:
            move_file_atomic(str(file_path), str(done_file))
            print(f"📁 Moved to Done: {file_path.name}")
        except Exception as e:
            print(f"❌ Failed to move to Done: {e}")

    def handle_corrupted_file(self, file_path: str):
        """Handle corrupted approval file.

        Moves file to quarantine and creates alert in Needs_Action.

        Args:
            file_path: Path to corrupted file
        """
        file_path = Path(file_path)

        print(f"🚨 Corrupted file detected: {file_path.name}")

        # Create quarantine and needs_action directories
        self.quarantine.mkdir(parents=True, exist_ok=True)
        self.needs_action.mkdir(parents=True, exist_ok=True)

        # Move to quarantine
        quarantine_file = self.quarantine / file_path.name
        try:
            move_file_atomic(str(file_path), str(quarantine_file))
            print(f"📦 Quarantined: {file_path.name}")
        except Exception as e:
            print(f"❌ Failed to quarantine: {e}")
            return

        # Create alert
        timestamp = datetime.now(UTC).strftime('%Y%m%d_%H%M%S')
        alert_file = self.needs_action / f"ALERT_{timestamp}_corrupted_approval.md"

        content = f"""---
alert_type: corrupted_approval_file
created_at: {datetime.now(UTC).isoformat()}Z
corrupted_file: {file_path.name}
quarantine_location: .quarantine/{file_path.name}
status: needs_attention
---

# Corrupted Approval File Alert

**File:** {file_path.name}
**Timestamp:** {datetime.now(UTC).isoformat()}Z
**Location:** Quarantined in `.quarantine/`

## Issue

The approval file could not be validated against the schema. It may have:
- Invalid JSON/YAML format
- Missing required fields
- Corrupted frontmatter

## Recommended Actions

- [ ] Review quarantined file: `.quarantine/{file_path.name}`
- [ ] Check file format and required fields
- [ ] Recreate approval file if needed
- [ ] Validate against schema: `specs/001-gmail-approval-workflow/contracts/approval-request.schema.json`

## Notes

(Add your investigation notes here)
"""

        with open(alert_file, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"🚨 Created alert: {alert_file.name}")

    def create_plan(self, approval_file_path: str) -> str:
        """Create Plan.md before executing action.

        Args:
            approval_file_path: Path to approval file

        Returns:
            Path to created plan file
        """
        approval_file = Path(approval_file_path)

        # Parse approval file
        with open(approval_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract frontmatter
        match = re.search(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
        if not match:
            raise ValueError("Invalid approval file format")

        frontmatter = match.group(1).strip()

        # Try to parse as JSON or YAML
        try:
            data = json.loads(frontmatter)
        except json.JSONDecodeError:
            # Use YAML parser for proper nested structure handling
            try:
                data = yaml.safe_load(frontmatter)
            except yaml.YAMLError:
                raise ValueError("Invalid approval file format: cannot parse frontmatter")

        # Generate plan
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        plan_file = self.vault_path / 'Plans' / f"PLAN_{timestamp}_{data.get('action_type', 'action')}.md"

        self.vault_path.joinpath('Plans').mkdir(parents=True, exist_ok=True)

        plan_content = f"""---
plan_id: plan_{timestamp}
approval_ref: {data.get('approval_id', 'unknown')}
action_type: {data.get('action_type', 'unknown')}
created_at: {datetime.utcnow().isoformat()}Z
---

# Action Plan

**Approval Reference:** {data.get('approval_id', 'unknown')}
**Action Type:** {data.get('action_type', 'unknown')}
**Risk Assessment:** {data.get('risk_assessment', 'unknown')}

## Problem Statement

Execute approved action: {data.get('action_type', 'unknown')}

## Analysis

This action has been approved by human review and is ready for execution.

**Reasoning:** {data.get('reasoning', 'No reasoning provided')}

## Alternatives Considered

1. **Execute immediately** (Chosen)
   - Pros: Timely response, follows approval
   - Cons: None identified

2. **Delay execution**
   - Pros: Additional review time
   - Cons: Delays response, not necessary after approval

## Chosen Approach

Execute the approved action via MCP with proper error handling and logging.

## Expected Outcomes

- Action executed successfully
- Log entry created with complete audit trail
- File moved to Done/ folder

## Risk Mitigation

- Retry logic with exponential backoff (max 3 attempts)
- Rate limit detection and handling
- Comprehensive error logging
- Dry-run mode support
"""

        with open(plan_file, 'w', encoding='utf-8') as f:
            f.write(plan_content)

        print(f"📋 Created plan: {plan_file.name}")
        return str(plan_file)

    def execute_approved_action(self, approval_file_path: str):
        """Execute approved action via MCP.

        Args:
            approval_file_path: Path to approval file
        """
        approval_file = Path(approval_file_path)

        print(f"⚡ Executing: {approval_file.name}")

        # Create plan first (constitution requirement)
        plan_file = self.create_plan(str(approval_file))

        # Parse approval file
        with open(approval_file, 'r', encoding='utf-8') as f:
            content = f.read()

        match = re.search(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
        if not match:
            raise ValueError("Invalid approval file format")

        frontmatter = match.group(1).strip()

        try:
            data = json.loads(frontmatter)
        except json.JSONDecodeError:
            # Use YAML parser for proper nested structure handling
            try:
                data = yaml.safe_load(frontmatter)
            except yaml.YAMLError:
                raise ValueError("Invalid approval file format: cannot parse frontmatter")

        # Check dry-run mode
        config = load_config()
        if config.get('dry_run', False):
            print(f"🔍 DRY RUN: Would execute {data.get('action_type', 'unknown')}")
            log_entry = {
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'log_id': f"dryrun_{int(datetime.utcnow().timestamp())}",
                'action_type': 'dry_run_execution',
                'approval_id': data.get('approval_id'),
                'status': 'success',
                'inputs': data.get('action_params', {}),
                'outputs': {'note': 'Dry run - no actual execution'}
            }
            create_log_entry(str(self.logs), log_entry)
        else:
            # Execute action via MCP
            try:
                result = self._send_email_via_mcp(data.get('action_params', {}))

                # Create success log entry
                log_entry = {
                    'timestamp': datetime.utcnow().isoformat() + 'Z',
                    'log_id': f"exec_{int(datetime.utcnow().timestamp())}",
                    'action_type': 'email_sent',
                    'email_id': data.get('email_action_ref'),
                    'approval_id': data.get('approval_id'),
                    'status': 'success',
                    'inputs': data.get('action_params', {}),
                    'outputs': result
                }
                create_log_entry(str(self.logs), log_entry)

                print(f"✅ Executed successfully")

            except Exception as e:
                # Create failure log entry
                log_entry = {
                    'timestamp': datetime.utcnow().isoformat() + 'Z',
                    'log_id': f"exec_fail_{int(datetime.utcnow().timestamp())}",
                    'action_type': 'email_send_failed',
                    'email_id': data.get('email_action_ref'),
                    'approval_id': data.get('approval_id'),
                    'status': 'failure',
                    'inputs': data.get('action_params', {}),
                    'error_details': {
                        'error_type': type(e).__name__,
                        'error_message': str(e)
                    }
                }
                create_log_entry(str(self.logs), log_entry)

                print(f"❌ Execution failed: {e}")
                raise

        # Move to Done
        done_file = self.done / approval_file.name
        move_file_atomic(str(approval_file), str(done_file))
        print(f"📁 Moved to Done: {approval_file.name}")

    def _send_email_via_mcp(self, action_params: Dict[str, Any]) -> Dict[str, Any]:
        """Send email via MCP server.

        Args:
            action_params: Email parameters (recipient, subject, body)

        Returns:
            Execution result dictionary
        """
        # TODO: Implement actual MCP integration
        # For now, return mock success
        print(f"📧 Sending email to: {action_params.get('recipient')}")
        print(f"   Subject: {action_params.get('subject')}")

        return {
            'message_id': f"mock_{int(datetime.utcnow().timestamp())}",
            'status': 'sent',
            'recipient': action_params.get('recipient')
        }

    def check_incomplete_actions(self) -> list:
        """Check for incomplete actions in Approved folder.

        Returns:
            List of incomplete action file paths
        """
        if not self.approved.exists():
            return []

        incomplete = list(self.approved.glob("*.md"))
        if incomplete:
            print(f"⚠️ Found {len(incomplete)} incomplete actions")

        return [str(f) for f in incomplete]

    def _track_failure(self, error: Exception):
        """Track consecutive failures.

        Args:
            error: Exception that occurred
        """
        self.consecutive_failures += 1
        self.last_failure_time = datetime.utcnow()

        print(f"⚠️ Failure {self.consecutive_failures}: {str(error)}")

        # Create error report after max retries
        if self.consecutive_failures >= 3:
            self._create_error_report(error)

    def _create_error_report(self, error: Exception):
        """Create error report after max consecutive failures.

        Args:
            error: Last exception that occurred
        """
        needs_action_dir = self.needs_action
        needs_action_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        report_file = needs_action_dir / f"ERROR_REPORT_{timestamp}.md"

        content = f"""---
report_type: consecutive_failures
created_at: {datetime.utcnow().isoformat()}Z
failure_count: {self.consecutive_failures}
status: needs_attention
---

# Error Report: Consecutive Failures

**Failure Count:** {self.consecutive_failures}
**Last Failure:** {datetime.utcnow().isoformat()}Z
**Error Type:** {type(error).__name__}

## Error Details

```
{str(error)}
```

## Recommended Actions

- [ ] Review error logs in Logs/ folder
- [ ] Check system resources (disk space, memory)
- [ ] Verify network connectivity
- [ ] Check MCP server availability
- [ ] Restart approval executor after resolving issue

## Notes

The system has encountered {self.consecutive_failures} consecutive failures.
Manual intervention is required.
"""

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"📋 Created error report: {report_file.name}")

    def run(self):
        """Start monitoring vault folders for approval workflow.

        Uses watchdog Observer to monitor file movements and trigger actions.
        """
        import signal

        # Setup graceful shutdown handler
        def signal_handler(signum, frame):
            print("\n⏹️  Received shutdown signal, stopping observer...")
            if self.observer:
                self.observer.stop()
                self.observer.join()
            print("✅ Approval executor stopped gracefully")
            exit(0)

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

        print("=" * 60)
        print("📋 Approval Executor - Silver Tier")
        print("=" * 60)
        print(f"Vault: {self.vault_path}")
        print(f"Monitoring: Pending_Approval, Approved, Rejected")
        print("=" * 60)

        # Validate vault structure on startup
        from watchers.gmail_state import validate_vault_structure
        if not validate_vault_structure(str(self.vault_path)):
            print("❌ Vault structure validation failed")
            return

        # Check for incomplete actions on startup
        incomplete = self.check_incomplete_actions()
        if incomplete:
            print(f"⚠️ Found {len(incomplete)} incomplete actions in Approved/ folder")
            print("   Processing incomplete actions...")
            for action_file in incomplete:
                try:
                    self.on_file_moved_to_approved(action_file)
                except Exception as e:
                    print(f"❌ Failed to process {action_file}: {e}")

        # Create event handler
        event_handler = ApprovalFileHandler(self)

        # Create observer
        self.observer = Observer()

        # Watch folders
        self.observer.schedule(event_handler, str(self.pending_approval), recursive=False)
        self.observer.schedule(event_handler, str(self.approved), recursive=False)
        self.observer.schedule(event_handler, str(self.rejected), recursive=False)

        # Start observer
        self.observer.start()
        print("✅ Approval executor started")

        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            self.observer.stop()
            print("\n⏹️  Approval executor stopped")

        self.observer.join()


if __name__ == "__main__":
    """Entry point for running approval executor as a script."""
    executor = ApprovalExecutor()
    executor.run()
