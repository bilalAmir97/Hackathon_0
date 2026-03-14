#!/usr/bin/env python3
"""
Orchestrator with Ralph Loop Integration

Continuously monitors vault and processes tasks autonomously using Ralph Loop pattern.
"""

import sys
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


class TaskOrchestrator:
    """Orchestrates autonomous task processing with Ralph Loop pattern."""

    def __init__(self, vault_path: str = "AI_Employee_Vault"):
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / "Needs_Action"
        self.in_progress = self.vault_path / "In_Progress"
        self.done = self.vault_path / "Done"
        self.logs = self.vault_path / "Logs"

        # Ensure folders exist
        self.in_progress.mkdir(exist_ok=True)
        self.logs.mkdir(exist_ok=True)

        # Setup logging
        log_file = self.logs / f"orchestrator_{datetime.now().strftime('%Y%m%d')}.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def get_pending_tasks(self) -> List[Path]:
        """Get all pending tasks from Needs_Action."""
        tasks = []
        for task_file in self.needs_action.glob("*.md"):
            # Skip alerts and system files
            if task_file.name.startswith("ALERT_"):
                continue
            if task_file.name.startswith("EXAMPLE_"):
                continue
            tasks.append(task_file)
        return sorted(tasks, key=lambda x: x.stat().st_mtime)

    def claim_task(self, task_file: Path) -> Optional[Path]:
        """Move task to In_Progress to claim it."""
        try:
            dest = self.in_progress / task_file.name
            if dest.exists():
                self.logger.warning(f"Task already claimed: {task_file.name}")
                return None

            task_file.rename(dest)
            self.logger.info(f"✓ Claimed task: {task_file.name}")
            return dest
        except Exception as e:
            self.logger.error(f"Failed to claim task {task_file.name}: {e}")
            return None

    def process_task_with_ralph_loop(self, task_file: Path, max_iterations: int = 10) -> bool:
        """
        Process a task using Ralph Loop pattern.

        In a real implementation, this would:
        1. Read the task file
        2. Generate a prompt for Claude
        3. Run Claude Code
        4. Check if task moved to /Done
        5. Repeat until complete or max iterations

        For this implementation, we'll create a placeholder that shows the pattern.
        """
        self.logger.info(f"🔄 Starting Ralph Loop for: {task_file.name}")

        for iteration in range(1, max_iterations + 1):
            self.logger.info(f"--- Iteration {iteration}/{max_iterations} ---")

            # Check if task was completed (moved to Done)
            done_file = self.done / task_file.name
            if done_file.exists():
                self.logger.info(f"✅ Task completed: {task_file.name}")
                return True

            # Check if task still exists in In_Progress
            if not task_file.exists():
                self.logger.warning(f"⚠ Task file disappeared: {task_file.name}")
                return False

            # In real implementation, this would:
            # 1. Read task file
            # 2. Generate Claude prompt
            # 3. Run Claude Code
            # 4. Wait for completion

            self.logger.info(f"Processing task (iteration {iteration})...")

            # Simulate processing time
            time.sleep(2)

            # Check completion again
            if done_file.exists():
                self.logger.info(f"✅ Task completed: {task_file.name}")
                return True

        # Max iterations reached
        self.logger.warning(f"⚠ Max iterations reached for: {task_file.name}")
        self.create_incomplete_alert(task_file, max_iterations)
        return False

    def create_incomplete_alert(self, task_file: Path, iterations: int):
        """Create alert for incomplete task."""
        alert_file = self.needs_action / f"ALERT_RALPH_INCOMPLETE_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

        content = f"""---
type: alert
priority: high
status: pending
created: {datetime.now().isoformat()}
---

## Ralph Loop Incomplete

Task did not complete after {iterations} iterations.

**Task:** {task_file.name}
**Location:** {task_file}
**Iterations:** {iterations}

**Action Required:**
1. Review the task file
2. Check if task is too complex
3. Manually complete or restart with higher iteration limit

**Restart Command:**
```bash
uv run python scripts/ralph_loop.py --task "{task_file.name}" --max-iterations 20
```
"""
        alert_file.write_text(content)
        self.logger.info(f"⚠ Alert created: {alert_file.name}")

    def run_once(self):
        """Process all pending tasks once."""
        self.logger.info("=" * 60)
        self.logger.info("🤖 Orchestrator - Processing Pending Tasks")
        self.logger.info("=" * 60)

        pending_tasks = self.get_pending_tasks()

        if not pending_tasks:
            self.logger.info("No pending tasks")
            return

        self.logger.info(f"Found {len(pending_tasks)} pending task(s)")

        for task_file in pending_tasks:
            self.logger.info(f"\n📋 Processing: {task_file.name}")

            # Claim the task
            claimed_task = self.claim_task(task_file)
            if not claimed_task:
                continue

            # Process with Ralph Loop
            success = self.process_task_with_ralph_loop(claimed_task)

            if success:
                self.logger.info(f"✓ Task completed successfully: {task_file.name}")
            else:
                self.logger.warning(f"⚠ Task incomplete: {task_file.name}")

    def run_continuous(self, check_interval: int = 60):
        """Run continuously, checking for new tasks."""
        self.logger.info("🔄 Starting continuous orchestration")
        self.logger.info(f"Check interval: {check_interval}s")

        try:
            while True:
                self.run_once()
                self.logger.info(f"\n💤 Sleeping for {check_interval}s...")
                time.sleep(check_interval)
        except KeyboardInterrupt:
            self.logger.info("\n⏹️  Orchestrator stopped by user")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Task Orchestrator with Ralph Loop')
    parser.add_argument('--vault', default='AI_Employee_Vault', help='Vault path')
    parser.add_argument('--continuous', action='store_true', help='Run continuously')
    parser.add_argument('--interval', type=int, default=60, help='Check interval (seconds)')

    args = parser.parse_args()

    orchestrator = TaskOrchestrator(vault_path=args.vault)

    if args.continuous:
        orchestrator.run_continuous(check_interval=args.interval)
    else:
        orchestrator.run_once()


if __name__ == "__main__":
    main()
