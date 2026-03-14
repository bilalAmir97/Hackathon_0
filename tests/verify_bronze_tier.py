#!/usr/bin/env python3
"""
Bronze Tier Verification Test

Tests Bronze tier functionality after migration to root directory.
Does not require external dependencies (watchdog, etc.)
"""

import sys
from pathlib import Path
from datetime import datetime
import shutil


class BronzeTierVerifier:
    """Verify Bronze tier is working after migration"""

    def __init__(self):
        self.vault_path = Path('AI_Employee_Vault')
        self.tests_passed = 0
        self.tests_failed = 0

    def test(self, name: str, func) -> bool:
        """Run a test and record result"""
        try:
            print(f"\n{'─'*60}")
            print(f"Testing: {name}")
            print('─'*60)
            result = func()
            if result:
                print(f"✅ PASSED: {name}")
                self.tests_passed += 1
                return True
            else:
                print(f"❌ FAILED: {name}")
                self.tests_failed += 1
                return False
        except Exception as e:
            print(f"❌ ERROR in {name}: {str(e)}")
            self.tests_failed += 1
            return False

    def test_vault_structure(self) -> bool:
        """Test 1: Verify vault directory structure"""
        if not self.vault_path.exists():
            print(f"❌ Vault directory not found: {self.vault_path}")
            return False

        required_dirs = [
            'Inbox', 'Needs_Action', 'Done', 'Plans', 'Logs',
            'Pending_Approval', 'Approved', 'Rejected'
        ]

        missing = []
        for dir_name in required_dirs:
            dir_path = self.vault_path / dir_name
            if dir_path.exists():
                print(f"  ✓ {dir_name}/ exists")
            else:
                print(f"  ✗ {dir_name}/ missing")
                missing.append(dir_name)

        return len(missing) == 0

    def test_key_files(self) -> bool:
        """Test 2: Verify key files exist"""
        key_files = ['Dashboard.md', 'Company_Handbook.md']

        missing = []
        for file_name in key_files:
            file_path = self.vault_path / file_name
            if file_path.exists():
                size = file_path.stat().st_size
                print(f"  ✓ {file_name} exists ({size} bytes)")
            else:
                print(f"  ✗ {file_name} missing")
                missing.append(file_name)

        return len(missing) == 0

    def test_file_operations(self) -> bool:
        """Test 3: Test file creation and movement"""
        # Create test file in Inbox
        test_file = self.vault_path / 'Inbox' / 'TEST_bronze_verification.txt'
        test_content = f"Bronze tier verification test\nTimestamp: {datetime.now()}"

        print(f"  Creating test file: {test_file.name}")
        test_file.write_text(test_content)

        if not test_file.exists():
            print(f"  ✗ Failed to create test file")
            return False
        print(f"  ✓ Test file created in Inbox")

        # Simulate watcher creating action item
        action_item = self.vault_path / 'Needs_Action' / 'TEST_ACTION_bronze_verification.md'
        action_content = f"""---
type: test
status: pending
created: {datetime.now().isoformat()}
---

## Test Action Item

This is a test action item created during Bronze tier verification.

Original file: {test_file.name}

## Actions
- [x] Verify file creation
- [x] Verify action item creation
- [ ] Move to Done
"""
        print(f"  Creating action item: {action_item.name}")
        action_item.write_text(action_content)

        if not action_item.exists():
            print(f"  ✗ Failed to create action item")
            return False
        print(f"  ✓ Action item created in Needs_Action")

        # Move files to Done (simulating completion)
        done_file = self.vault_path / 'Done' / test_file.name
        done_action = self.vault_path / 'Done' / action_item.name

        print(f"  Moving files to Done...")
        shutil.move(str(test_file), str(done_file))
        shutil.move(str(action_item), str(done_action))

        if done_file.exists() and done_action.exists():
            print(f"  ✓ Files moved to Done successfully")
        else:
            print(f"  ✗ Failed to move files to Done")
            return False

        # Cleanup
        done_file.unlink()
        done_action.unlink()
        print(f"  ✓ Test files cleaned up")

        return True

    def test_watchers_module(self) -> bool:
        """Test 4: Verify watchers module structure"""
        watchers_path = Path('watchers')

        if not watchers_path.exists():
            print(f"  ✗ Watchers directory not found")
            return False
        print(f"  ✓ Watchers directory exists")

        required_files = ['__init__.py', 'base_watcher.py', 'filesystem_watcher.py']
        missing = []

        for file_name in required_files:
            file_path = watchers_path / file_name
            if file_path.exists():
                size = file_path.stat().st_size
                print(f"  ✓ {file_name} exists ({size} bytes)")
            else:
                print(f"  ✗ {file_name} missing")
                missing.append(file_name)

        return len(missing) == 0

    def test_dashboard_content(self) -> bool:
        """Test 5: Verify Dashboard.md has valid content"""
        dashboard = self.vault_path / 'Dashboard.md'

        if not dashboard.exists():
            print(f"  ✗ Dashboard.md not found")
            return False

        content = dashboard.read_text()

        required_sections = [
            '# AI Employee Dashboard',
            '## System Status',
            '## Recent Activity',
            '## Quick Stats'
        ]

        missing = []
        for section in required_sections:
            if section in content:
                print(f"  ✓ Found section: {section}")
            else:
                print(f"  ✗ Missing section: {section}")
                missing.append(section)

        return len(missing) == 0

    def test_handbook_content(self) -> bool:
        """Test 6: Verify Company_Handbook.md has valid content"""
        handbook = self.vault_path / 'Company_Handbook.md'

        if not handbook.exists():
            print(f"  ✗ Company_Handbook.md not found")
            return False

        content = handbook.read_text()

        required_sections = [
            '# Company Handbook',
            '## Core Principles',
            '## Rules of Engagement',
            '## Approval Requirements'
        ]

        missing = []
        for section in required_sections:
            if section in content:
                print(f"  ✓ Found section: {section}")
            else:
                print(f"  ✗ Missing section: {section}")
                missing.append(section)

        return len(missing) == 0

    def test_path_references(self) -> bool:
        """Test 7: Verify no old Bronze/ path references"""
        print("  Checking for old path references...")

        # Check test scripts
        test_files = list(Path('tests').glob('*.py'))
        old_path_found = False

        for test_file in test_files:
            content = test_file.read_text()
            if 'Bronze/AI_Employee_Vault' in content:
                print(f"  ✗ Old path found in: {test_file.name}")
                old_path_found = True

        if not old_path_found:
            print(f"  ✓ No old path references in test files")

        # Check orchestrator
        orchestrator = Path('scripts/orchestrator.py')
        if orchestrator.exists():
            content = orchestrator.read_text()
            if 'Bronze/AI_Employee_Vault' in content:
                print(f"  ✗ Old path found in: orchestrator.py")
                old_path_found = True
            else:
                print(f"  ✓ No old path references in orchestrator")

        return not old_path_found

    def run_all_tests(self):
        """Run all verification tests"""
        print("\n" + "="*60)
        print("🧪 Bronze Tier Verification - Post-Migration")
        print("="*60)

        self.test("Vault Structure", self.test_vault_structure)
        self.test("Key Files", self.test_key_files)
        self.test("File Operations", self.test_file_operations)
        self.test("Watchers Module", self.test_watchers_module)
        self.test("Dashboard Content", self.test_dashboard_content)
        self.test("Handbook Content", self.test_handbook_content)
        self.test("Path References", self.test_path_references)

        # Print summary
        print("\n" + "="*60)
        print("📊 Verification Summary")
        print("="*60)

        total = self.tests_passed + self.tests_failed
        success_rate = (self.tests_passed / total * 100) if total > 0 else 0

        print(f"✅ Passed: {self.tests_passed}/{total}")
        print(f"❌ Failed: {self.tests_failed}/{total}")
        print(f"🎯 Success Rate: {success_rate:.1f}%")
        print("="*60)

        if self.tests_failed == 0:
            print("\n🎉 Bronze Tier is fully functional after migration!")
            print("\nNext steps:")
            print("  1. Install dependencies: pip install watchdog")
            print("  2. Test file system watcher: python watchers/filesystem_watcher.py")
            print("  3. Start Silver tier implementation")
            return True
        else:
            print("\n⚠️  Some tests failed. Please review the output above.")
            return False


def main():
    """Main entry point"""
    verifier = BronzeTierVerifier()
    success = verifier.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
