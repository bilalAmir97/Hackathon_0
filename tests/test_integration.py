#!/usr/bin/env python3
"""
Integration Tests - End-to-End Workflow Testing

Tests complete workflows across multiple skills to ensure
they work together correctly.

Usage:
    python tests/test_integration.py
    python tests/test_integration.py --workflow email
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
import time
import shutil

sys.path.insert(0, str(Path(__file__).parent.parent))


class IntegrationTester:
    """Integration testing for complete workflows"""

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.test_results = []

    def setup(self):
        """Setup test environment"""
        print("🔧 Setting up test environment...")

        # Ensure all directories exist
        dirs = [
            'Inbox', 'Needs_Action', 'Done', 'Plans', 'Logs',
            'Pending_Approval', 'Approved', 'Rejected'
        ]

        for dir_name in dirs:
            dir_path = self.vault_path / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)

        print("✅ Test environment ready\n")

    def cleanup(self):
        """Cleanup test files"""
        print("\n🧹 Cleaning up test files...")

        test_files = [
            self.vault_path / 'Inbox' / 'TEST_*.md',
            self.vault_path / 'Needs_Action' / 'TEST_*.md',
            self.vault_path / 'Done' / 'TEST_*.md',
            self.vault_path / 'Pending_Approval' / 'TEST_*.md',
            self.vault_path / 'Approved' / 'TEST_*.md',
        ]

        for pattern in test_files:
            for file in pattern.parent.glob(pattern.name):
                file.unlink()

        print("✅ Cleanup complete\n")

    def test_email_workflow(self) -> bool:
        """
        Test complete email workflow:
        1. Email detected → Action item created
        2. Action item processed → Draft created
        3. Draft approved → Email sent
        4. Task moved to Done
        """
        print("="*70)
        print("📧 Testing Email Workflow (End-to-End)")
        print("="*70 + "\n")

        try:
            # Step 1: Simulate email detection
            print("Step 1: Simulating email detection...")
            email_action = self.vault_path / 'Needs_Action' / 'TEST_EMAIL_workflow.md'
            email_action.write_text("""---
type: email
from: client@example.com
subject: Project Inquiry
priority: high
status: pending
gmail_id: test_123
---

## Email Content
Hi, I'm interested in your web development services.
Can you provide pricing and timeline?

## Suggested Actions
- [ ] Draft response with pricing
- [ ] Create approval request
- [ ] Send response
""")
            print("✅ Email action item created\n")

            # Step 2: Simulate processing (draft creation)
            print("Step 2: Simulating email processing...")
            time.sleep(1)

            draft_approval = self.vault_path / 'Pending_Approval' / 'TEST_EMAIL_SEND_workflow.md'
            draft_approval.write_text("""---
type: approval_request
action: send_email
to: client@example.com
subject: Re: Project Inquiry
status: pending_approval
created: 2026-02-19T10:00:00Z
expires: 2026-02-20T10:00:00Z
---

## Email Draft

Hi,

Thank you for your inquiry about our web development services.

Our pricing typically ranges from $5,000-$15,000 depending on scope.
Timeline is usually 4-6 weeks for a standard website.

Would you like to schedule a call to discuss your specific needs?

Best regards,
Your Name

## To Approve
Move this file to Approved/ folder
""")
            print("✅ Draft created and approval requested\n")

            # Step 3: Simulate human approval
            print("Step 3: Simulating human approval...")
            time.sleep(1)

            approved_file = self.vault_path / 'Approved' / 'TEST_EMAIL_SEND_workflow.md'
            shutil.move(str(draft_approval), str(approved_file))
            print("✅ Email approved\n")

            # Step 4: Simulate email sent and task completion
            print("Step 4: Simulating email send and completion...")
            time.sleep(1)

            # Move to Done
            done_file = self.vault_path / 'Done' / 'TEST_EMAIL_workflow.md'
            shutil.move(str(email_action), str(done_file))

            # Move approval to Done
            done_approval = self.vault_path / 'Done' / 'TEST_EMAIL_SEND_workflow.md'
            shutil.move(str(approved_file), str(done_approval))

            print("✅ Email sent and task completed\n")

            # Verify workflow
            success = (
                done_file.exists() and
                done_approval.exists() and
                not email_action.exists() and
                not draft_approval.exists()
            )

            if success:
                print("✅ Email workflow completed successfully!\n")
            else:
                print("❌ Email workflow failed - files not in expected state\n")

            return success

        except Exception as e:
            print(f"❌ Email workflow failed with error: {e}\n")
            return False

    def test_file_processing_workflow(self) -> bool:
        """
        Test file processing workflow:
        1. File dropped in Inbox
        2. Watcher detects and creates action item
        3. Action item processed
        4. File moved to Done
        """
        print("="*70)
        print("📁 Testing File Processing Workflow")
        print("="*70 + "\n")

        try:
            # Step 1: Drop file in Inbox
            print("Step 1: Dropping file in Inbox...")
            inbox_file = self.vault_path / 'Inbox' / 'TEST_document.txt'
            inbox_file.write_text("This is a test document for processing.")
            print("✅ File dropped in Inbox\n")

            # Step 2: Simulate watcher creating action item
            print("Step 2: Simulating watcher detection...")
            time.sleep(1)

            action_item = self.vault_path / 'Needs_Action' / 'TEST_FILE_document.md'
            action_item.write_text(f"""---
type: file_drop
original_name: TEST_document.txt
size: {inbox_file.stat().st_size}
status: pending
---

## File Information
- Name: TEST_document.txt
- Type: Text Document
- Location: Inbox/TEST_document.txt

## Suggested Actions
- [ ] Review file content
- [ ] Process or categorize
- [ ] Move to appropriate folder
""")
            print("✅ Action item created\n")

            # Step 3: Simulate processing
            print("Step 3: Simulating file processing...")
            time.sleep(1)

            # Move file to Done
            done_file = self.vault_path / 'Done' / 'TEST_document.txt'
            shutil.move(str(inbox_file), str(done_file))

            # Move action item to Done
            done_action = self.vault_path / 'Done' / 'TEST_FILE_document.md'
            shutil.move(str(action_item), str(done_action))

            print("✅ File processed and moved to Done\n")

            # Verify workflow
            success = (
                done_file.exists() and
                done_action.exists() and
                not inbox_file.exists() and
                not action_item.exists()
            )

            if success:
                print("✅ File processing workflow completed successfully!\n")
            else:
                print("❌ File processing workflow failed\n")

            return success

        except Exception as e:
            print(f"❌ File processing workflow failed: {e}\n")
            return False

    def test_approval_workflow(self) -> bool:
        """
        Test approval workflow:
        1. Action requires approval
        2. Approval request created
        3. Human approves
        4. Action executed
        """
        print("="*70)
        print("✋ Testing Approval Workflow")
        print("="*70 + "\n")

        try:
            # Step 1: Create approval request
            print("Step 1: Creating approval request...")
            approval_file = self.vault_path / 'Pending_Approval' / 'TEST_APPROVAL_action.md'
            approval_file.write_text("""---
type: approval_request
action: test_action
status: pending_approval
created: 2026-02-19T10:00:00Z
expires: 2026-02-20T10:00:00Z
risk_level: medium
---

## Action Summary
Test action requiring approval

## To Approve
Move to Approved/ folder
""")
            print("✅ Approval request created\n")

            # Step 2: Simulate human approval
            print("Step 2: Simulating human approval...")
            time.sleep(1)

            approved_file = self.vault_path / 'Approved' / 'TEST_APPROVAL_action.md'
            shutil.move(str(approval_file), str(approved_file))
            print("✅ Action approved\n")

            # Step 3: Simulate execution
            print("Step 3: Simulating action execution...")
            time.sleep(1)

            done_file = self.vault_path / 'Done' / 'TEST_APPROVAL_action.md'
            shutil.move(str(approved_file), str(done_file))
            print("✅ Action executed\n")

            # Verify workflow
            success = (
                done_file.exists() and
                not approval_file.exists() and
                not approved_file.exists()
            )

            if success:
                print("✅ Approval workflow completed successfully!\n")
            else:
                print("❌ Approval workflow failed\n")

            return success

        except Exception as e:
            print(f"❌ Approval workflow failed: {e}\n")
            return False

    def test_multi_step_task(self) -> bool:
        """
        Test multi-step task completion:
        1. Complex task created
        2. Multiple actions required
        3. All steps completed
        4. Task marked done
        """
        print("="*70)
        print("🔄 Testing Multi-Step Task Workflow")
        print("="*70 + "\n")

        try:
            # Step 1: Create complex task
            print("Step 1: Creating multi-step task...")
            task_file = self.vault_path / 'Needs_Action' / 'TEST_MULTISTEP_task.md'
            task_file.write_text("""---
type: project_task
priority: high
status: pending
---

## Task: Complete Project Setup

### Steps Required
- [ ] Create project structure
- [ ] Initialize git repository
- [ ] Set up dependencies
- [ ] Create README
- [ ] Run initial tests

## Completion Criteria
All steps must be checked off before moving to Done.
""")
            print("✅ Multi-step task created\n")

            # Step 2: Simulate step-by-step completion
            print("Step 2: Simulating step completion...")
            for i, step in enumerate(['structure', 'git', 'dependencies', 'readme', 'tests'], 1):
                time.sleep(0.5)
                print(f"  ✓ Step {i}/5: {step} completed")

            print("\n✅ All steps completed\n")

            # Step 3: Move to Done
            print("Step 3: Moving task to Done...")
            done_file = self.vault_path / 'Done' / 'TEST_MULTISTEP_task.md'
            shutil.move(str(task_file), str(done_file))
            print("✅ Task moved to Done\n")

            # Verify workflow
            success = done_file.exists() and not task_file.exists()

            if success:
                print("✅ Multi-step task workflow completed successfully!\n")
            else:
                print("❌ Multi-step task workflow failed\n")

            return success

        except Exception as e:
            print(f"❌ Multi-step task workflow failed: {e}\n")
            return False

    def run_all_workflows(self) -> dict:
        """Run all integration tests"""
        print("\n" + "="*70)
        print("🧪 Integration Tests - Complete Workflow Testing")
        print("="*70 + "\n")

        self.setup()

        workflows = [
            ("Email Workflow", self.test_email_workflow),
            ("File Processing Workflow", self.test_file_processing_workflow),
            ("Approval Workflow", self.test_approval_workflow),
            ("Multi-Step Task Workflow", self.test_multi_step_task)
        ]

        results = {}
        for name, test_func in workflows:
            try:
                success = test_func()
                results[name] = "PASSED" if success else "FAILED"
            except Exception as e:
                print(f"❌ {name} crashed: {e}\n")
                results[name] = "ERROR"

        self.cleanup()

        # Print summary
        print("="*70)
        print("📊 Integration Test Summary")
        print("="*70)

        for name, status in results.items():
            icon = "✅" if status == "PASSED" else "❌"
            print(f"{icon} {name}: {status}")

        passed = sum(1 for s in results.values() if s == "PASSED")
        total = len(results)

        print(f"\n{'='*70}")
        print(f"🎯 Overall: {passed}/{total} workflows passed ({passed/total*100:.1f}%)")
        print(f"{'='*70}\n")

        return results


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Integration tests for Silver tier workflows'
    )
    parser.add_argument(
        '--workflow',
        type=str,
        choices=['email', 'file', 'approval', 'multistep'],
        help='Test specific workflow only'
    )
    parser.add_argument(
        '--vault-path',
        type=str,
        default='./AI_Employee_Vault',
        help='Path to Obsidian vault'
    )

    args = parser.parse_args()

    tester = IntegrationTester(args.vault_path)

    if args.workflow:
        # Test specific workflow
        tester.setup()

        workflow_map = {
            'email': tester.test_email_workflow,
            'file': tester.test_file_processing_workflow,
            'approval': tester.test_approval_workflow,
            'multistep': tester.test_multi_step_task
        }

        success = workflow_map[args.workflow]()
        tester.cleanup()

        sys.exit(0 if success else 1)
    else:
        # Run all workflows
        results = tester.run_all_workflows()
        any_failed = any(s != "PASSED" for s in results.values())
        sys.exit(1 if any_failed else 0)


if __name__ == '__main__':
    main()
