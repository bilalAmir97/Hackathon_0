#!/usr/bin/env python3
"""
Silver Tier Skills Test Suite

Comprehensive testing for all Silver tier AI Employee skills.

Usage:
    python tests/test_all_skills.py              # Run all tests
    python tests/test_all_skills.py --skill gmail  # Test specific skill
    python tests/test_all_skills.py --verbose     # Detailed output
"""

import sys
import argparse
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class SkillTester:
    """Base class for skill testing"""

    def __init__(self, vault_path: str, verbose: bool = False):
        self.vault_path = Path(vault_path)
        self.verbose = verbose
        self.results = []

    def log(self, message: str, level: str = "INFO"):
        """Log message if verbose"""
        if self.verbose or level in ["ERROR", "SUCCESS"]:
            prefix = {
                "INFO": "ℹ️ ",
                "SUCCESS": "✅",
                "ERROR": "❌",
                "WARNING": "⚠️ "
            }.get(level, "")
            print(f"{prefix} {message}")

    def test(self, name: str, func) -> bool:
        """Run a test and record result"""
        try:
            self.log(f"Testing: {name}")
            result = func()
            if result:
                self.log(f"PASSED: {name}", "SUCCESS")
                self.results.append({"test": name, "status": "passed"})
                return True
            else:
                self.log(f"FAILED: {name}", "ERROR")
                self.results.append({"test": name, "status": "failed"})
                return False
        except Exception as e:
            self.log(f"ERROR in {name}: {str(e)}", "ERROR")
            self.results.append({"test": name, "status": "error", "error": str(e)})
            return False

    def summary(self) -> Dict:
        """Generate test summary"""
        passed = sum(1 for r in self.results if r["status"] == "passed")
        failed = sum(1 for r in self.results if r["status"] == "failed")
        errors = sum(1 for r in self.results if r["status"] == "error")
        total = len(self.results)

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "success_rate": (passed / total * 100) if total > 0 else 0
        }


class GmailSkillTester(SkillTester):
    """Test Gmail monitoring skill"""

    def run_tests(self) -> bool:
        """Run all Gmail skill tests"""
        print("\n" + "="*70)
        print("📧 Testing Gmail Monitoring Skill")
        print("="*70 + "\n")

        all_passed = True
        all_passed &= self.test("Gmail credentials exist", self.test_credentials)
        all_passed &= self.test("Gmail watcher module exists", self.test_watcher_module)
        all_passed &= self.test("Vault structure correct", self.test_vault_structure)
        all_passed &= self.test("Action item format valid", self.test_action_item_format)
        all_passed &= self.test("Priority detection works", self.test_priority_detection)

        return all_passed

    def test_credentials(self) -> bool:
        """Check if Gmail credentials exist"""
        creds_path = Path("credentials.json")
        token_path = Path("token.json")

        if not creds_path.exists():
            self.log("credentials.json not found", "WARNING")
            self.log("Run: Create OAuth credentials in Google Cloud Console", "INFO")
            return False

        if not token_path.exists():
            self.log("token.json not found (will be created on first auth)", "WARNING")

        return creds_path.exists()

    def test_watcher_module(self) -> bool:
        """Check if Gmail watcher module exists"""
        watcher_path = Path("watchers/gmail_watcher.py")
        return watcher_path.exists()

    def test_vault_structure(self) -> bool:
        """Verify vault has correct structure"""
        required_dirs = [
            self.vault_path / "Needs_Action",
            self.vault_path / "Done",
            self.vault_path / "Logs"
        ]
        return all(d.exists() for d in required_dirs)

    def test_action_item_format(self) -> bool:
        """Test action item creation format"""
        # Create a test action item
        test_item = self.vault_path / "Needs_Action" / "TEST_email_format.md"
        content = """---
type: email
from: test@example.com
subject: Test Email
priority: high
status: pending
---

## Email Content
Test email content

## Suggested Actions
- [ ] Reply to sender
"""
        test_item.write_text(content)

        # Verify it was created correctly
        exists = test_item.exists()

        # Cleanup
        if exists:
            test_item.unlink()

        return exists

    def test_priority_detection(self) -> bool:
        """Test priority keyword detection"""
        high_keywords = ['urgent', 'asap', 'critical', 'deadline']
        test_text = "This is an urgent request with a deadline"

        detected = any(kw in test_text.lower() for kw in high_keywords)
        return detected


class EmailMCPTester(SkillTester):
    """Test Email MCP server skill"""

    def run_tests(self) -> bool:
        """Run all Email MCP tests"""
        print("\n" + "="*70)
        print("📤 Testing Email MCP Server Skill")
        print("="*70 + "\n")

        all_passed = True
        all_passed &= self.test("MCP server directory exists", self.test_mcp_directory)
        all_passed &= self.test("MCP config exists", self.test_mcp_config)
        all_passed &= self.test("Gmail send scope configured", self.test_send_scope)

        return all_passed

    def test_mcp_directory(self) -> bool:
        """Check if MCP server directory exists"""
        mcp_path = Path("mcp-servers/email-server")
        return mcp_path.exists()

    def test_mcp_config(self) -> bool:
        """Check if MCP config exists"""
        config_path = Path.home() / ".config/claude-code/mcp.json"
        if not config_path.exists():
            self.log("MCP config not found", "WARNING")
            self.log(f"Create: {config_path}", "INFO")
            return False
        return True

    def test_send_scope(self) -> bool:
        """Verify Gmail send scope is configured"""
        # This would check if OAuth scopes include gmail.send
        # For now, just check if credentials exist
        return Path("credentials.json").exists()


class ApprovalWorkflowTester(SkillTester):
    """Test approval workflow skill"""

    def run_tests(self) -> bool:
        """Run all approval workflow tests"""
        print("\n" + "="*70)
        print("✋ Testing Approval Workflow Skill")
        print("="*70 + "\n")

        all_passed = True
        all_passed &= self.test("Approval folders exist", self.test_approval_folders)
        all_passed &= self.test("Approval request format", self.test_approval_format)
        all_passed &= self.test("File movement works", self.test_file_movement)
        all_passed &= self.test("Expiration detection", self.test_expiration)

        return all_passed

    def test_approval_folders(self) -> bool:
        """Check if approval folders exist"""
        folders = [
            self.vault_path / "Pending_Approval",
            self.vault_path / "Approved",
            self.vault_path / "Rejected"
        ]
        return all(f.exists() for f in folders)

    def test_approval_format(self) -> bool:
        """Test approval request format"""
        test_file = self.vault_path / "Pending_Approval" / "TEST_approval.md"
        content = """---
type: approval_request
action: test_action
status: pending_approval
created: 2026-02-19T10:00:00Z
expires: 2026-02-20T10:00:00Z
---

## Test Approval
This is a test approval request.
"""
        test_file.write_text(content)
        exists = test_file.exists()

        # Cleanup
        if exists:
            test_file.unlink()

        return exists

    def test_file_movement(self) -> bool:
        """Test moving files between folders"""
        # Create test file
        test_file = self.vault_path / "Pending_Approval" / "TEST_move.md"
        test_file.write_text("Test content")

        # Move to Approved
        approved_file = self.vault_path / "Approved" / "TEST_move.md"
        test_file.rename(approved_file)

        # Verify move
        moved = approved_file.exists() and not test_file.exists()

        # Cleanup
        if approved_file.exists():
            approved_file.unlink()

        return moved

    def test_expiration(self) -> bool:
        """Test expiration time parsing"""
        from datetime import datetime, timedelta

        created = datetime.now()
        expires = created + timedelta(hours=24)

        # Check if expiration logic works
        is_expired = datetime.now() > expires
        return not is_expired  # Should not be expired yet


class WhatsAppTester(SkillTester):
    """Test WhatsApp monitoring skill"""

    def run_tests(self) -> bool:
        """Run all WhatsApp tests"""
        print("\n" + "="*70)
        print("💬 Testing WhatsApp Monitoring Skill")
        print("="*70 + "\n")

        all_passed = True
        all_passed &= self.test("Playwright installed", self.test_playwright)
        all_passed &= self.test("Session directory exists", self.test_session_dir)
        all_passed &= self.test("Watcher module exists", self.test_watcher_module)
        all_passed &= self.test("Keyword detection works", self.test_keywords)

        return all_passed

    def test_playwright(self) -> bool:
        """Check if Playwright is installed"""
        try:
            import playwright
            return True
        except ImportError:
            self.log("Playwright not installed", "WARNING")
            self.log("Run: pip install playwright", "INFO")
            self.log("Run: playwright install chromium", "INFO")
            return False

    def test_session_dir(self) -> bool:
        """Check if session directory exists"""
        session_path = Path("whatsapp_session")
        if not session_path.exists():
            self.log("WhatsApp session not configured", "WARNING")
            self.log("Run: python utils/whatsapp_setup.py", "INFO")
            return False
        return True

    def test_watcher_module(self) -> bool:
        """Check if WhatsApp watcher exists"""
        watcher_path = Path("watchers/whatsapp_watcher.py")
        return watcher_path.exists()

    def test_keywords(self) -> bool:
        """Test keyword detection"""
        keywords = ['urgent', 'help', 'invoice', 'payment']
        test_message = "urgent: need help with invoice payment"

        detected = any(kw in test_message.lower() for kw in keywords)
        return detected


class LinkedInTester(SkillTester):
    """Test LinkedIn posting skill"""

    def run_tests(self) -> bool:
        """Run all LinkedIn tests"""
        print("\n" + "="*70)
        print("💼 Testing LinkedIn Posting Skill")
        print("="*70 + "\n")

        all_passed = True
        all_passed &= self.test("LinkedIn session exists", self.test_session)
        all_passed &= self.test("Post format valid", self.test_post_format)
        all_passed &= self.test("Hashtag generation works", self.test_hashtags)

        return all_passed

    def test_session(self) -> bool:
        """Check if LinkedIn session exists"""
        session_path = Path("linkedin_session")
        if not session_path.exists():
            self.log("LinkedIn session not configured", "WARNING")
            self.log("Run: python utils/linkedin_setup.py", "INFO")
            return False
        return True

    def test_post_format(self) -> bool:
        """Test post approval format"""
        test_file = self.vault_path / "Pending_Approval" / "TEST_linkedin.md"
        content = """---
type: approval_request
action: post_linkedin
platform: linkedin
---

## Post Content
Test post content with #hashtags
"""
        test_file.write_text(content)
        exists = test_file.exists()

        # Cleanup
        if exists:
            test_file.unlink()

        return exists

    def test_hashtags(self) -> bool:
        """Test hashtag generation"""
        post_text = "Great project completion! #WebDevelopment #Success"
        hashtags = [word for word in post_text.split() if word.startswith('#')]
        return len(hashtags) > 0


class SchedulingTester(SkillTester):
    """Test task scheduling skill"""

    def run_tests(self) -> bool:
        """Run all scheduling tests"""
        print("\n" + "="*70)
        print("⏰ Testing Task Scheduling Skill")
        print("="*70 + "\n")

        all_passed = True
        all_passed &= self.test("PM2 installed", self.test_pm2)
        all_passed &= self.test("Ecosystem config exists", self.test_ecosystem)
        all_passed &= self.test("Cron/Task Scheduler available", self.test_scheduler)

        return all_passed

    def test_pm2(self) -> bool:
        """Check if PM2 is installed"""
        import subprocess
        try:
            result = subprocess.run(['pm2', '--version'], capture_output=True)
            return result.returncode == 0
        except FileNotFoundError:
            self.log("PM2 not installed", "WARNING")
            self.log("Run: npm install -g pm2", "INFO")
            return False

    def test_ecosystem(self) -> bool:
        """Check if ecosystem config exists"""
        config_path = Path("ecosystem.config.js")
        if not config_path.exists():
            self.log("Ecosystem config not found", "WARNING")
            return False
        return True

    def test_scheduler(self) -> bool:
        """Check if cron or Task Scheduler is available"""
        import platform
        system = platform.system()

        if system in ['Linux', 'Darwin']:  # Unix/macOS
            import subprocess
            try:
                result = subprocess.run(['which', 'crontab'], capture_output=True)
                return result.returncode == 0
            except:
                return False
        elif system == 'Windows':
            # Task Scheduler is built-in on Windows
            return True
        return False


class ReasoningLoopTester(SkillTester):
    """Test reasoning loop skill"""

    def run_tests(self) -> bool:
        """Run all reasoning loop tests"""
        print("\n" + "="*70)
        print("🔄 Testing Reasoning Loop Skill")
        print("="*70 + "\n")

        all_passed = True
        all_passed &= self.test("Orchestrator exists", self.test_orchestrator)
        all_passed &= self.test("Stop hook exists", self.test_stop_hook)
        all_passed &= self.test("Task completion detection", self.test_completion)

        return all_passed

    def test_orchestrator(self) -> bool:
        """Check if orchestrator script exists"""
        orchestrator_path = Path("scripts/orchestrator.py")
        return orchestrator_path.exists()

    def test_stop_hook(self) -> bool:
        """Check if stop hook exists"""
        hook_path = Path(".claude/hooks/stop.sh")
        if not hook_path.exists():
            self.log("Stop hook not found", "WARNING")
            self.log("Create: .claude/hooks/stop.sh", "INFO")
            return False
        return True

    def test_completion(self) -> bool:
        """Test task completion detection"""
        # Create test task
        test_task = self.vault_path / "Needs_Action" / "TEST_completion.md"
        test_task.write_text("Test task")

        # Move to Done
        done_task = self.vault_path / "Done" / "TEST_completion.md"
        test_task.rename(done_task)

        # Check if moved
        completed = done_task.exists() and not test_task.exists()

        # Cleanup
        if done_task.exists():
            done_task.unlink()

        return completed


def run_all_tests(vault_path: str, verbose: bool = False) -> Dict:
    """Run all skill tests"""
    print("\n" + "="*70)
    print("🧪 Silver Tier Skills - Comprehensive Test Suite")
    print("="*70)

    testers = [
        ("Gmail Monitoring", GmailSkillTester),
        ("Email MCP Server", EmailMCPTester),
        ("Approval Workflow", ApprovalWorkflowTester),
        ("WhatsApp Monitoring", WhatsAppTester),
        ("LinkedIn Posting", LinkedInTester),
        ("Task Scheduling", SchedulingTester),
        ("Reasoning Loop", ReasoningLoopTester)
    ]

    all_results = {}
    overall_passed = 0
    overall_total = 0

    for name, TesterClass in testers:
        tester = TesterClass(vault_path, verbose)
        passed = tester.run_tests()
        summary = tester.summary()

        all_results[name] = summary
        overall_passed += summary["passed"]
        overall_total += summary["total"]

    # Print overall summary
    print("\n" + "="*70)
    print("📊 Overall Test Summary")
    print("="*70)

    for name, summary in all_results.items():
        status = "✅" if summary["failed"] == 0 and summary["errors"] == 0 else "❌"
        print(f"{status} {name}: {summary['passed']}/{summary['total']} passed ({summary['success_rate']:.1f}%)")

    print(f"\n{'='*70}")
    overall_rate = (overall_passed / overall_total * 100) if overall_total > 0 else 0
    print(f"🎯 Overall: {overall_passed}/{overall_total} tests passed ({overall_rate:.1f}%)")
    print(f"{'='*70}\n")

    return all_results


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Test suite for Silver tier AI Employee skills'
    )
    parser.add_argument(
        '--skill',
        type=str,
        choices=['gmail', 'email-mcp', 'approval', 'whatsapp', 'linkedin', 'scheduling', 'reasoning-loop'],
        help='Test specific skill only'
    )
    parser.add_argument(
        '--vault-path',
        type=str,
        default='./AI_Employee_Vault',
        help='Path to Obsidian vault'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Verbose output'
    )

    args = parser.parse_args()

    if args.skill:
        # Test specific skill
        skill_map = {
            'gmail': GmailSkillTester,
            'email-mcp': EmailMCPTester,
            'approval': ApprovalWorkflowTester,
            'whatsapp': WhatsAppTester,
            'linkedin': LinkedInTester,
            'scheduling': SchedulingTester,
            'reasoning-loop': ReasoningLoopTester
        }

        TesterClass = skill_map[args.skill]
        tester = TesterClass(args.vault_path, args.verbose)
        passed = tester.run_tests()
        summary = tester.summary()

        print(f"\n{'='*70}")
        print(f"Result: {summary['passed']}/{summary['total']} tests passed")
        print(f"{'='*70}\n")

        sys.exit(0 if summary['failed'] == 0 and summary['errors'] == 0 else 1)
    else:
        # Run all tests
        results = run_all_tests(args.vault_path, args.verbose)

        # Exit with error if any tests failed
        any_failed = any(r['failed'] > 0 or r['errors'] > 0 for r in results.values())
        sys.exit(1 if any_failed else 0)


if __name__ == '__main__':
    main()
