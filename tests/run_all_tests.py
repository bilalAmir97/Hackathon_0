#!/usr/bin/env python3
"""
Master Test Runner

Runs all test suites in the correct order:
1. Environment verification
2. Unit tests (individual skills)
3. Integration tests (complete workflows)

Usage:
    python tests/run_all_tests.py
    python tests/run_all_tests.py --quick     # Skip integration tests
    python tests/run_all_tests.py --verbose   # Detailed output
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime


class TestRunner:
    """Master test runner for all test suites"""

    def __init__(self, verbose: bool = False, quick: bool = False):
        self.verbose = verbose
        self.quick = quick
        self.results = {}
        self.start_time = datetime.now()

    def run_command(self, name: str, command: list) -> bool:
        """Run a test command and capture result"""
        print(f"\n{'='*70}")
        print(f"🧪 Running: {name}")
        print(f"{'='*70}\n")

        try:
            result = subprocess.run(
                command,
                cwd=Path(__file__).parent.parent,
                capture_output=not self.verbose,
                text=True
            )

            success = result.returncode == 0

            if not self.verbose:
                # Print output if test failed
                if not success and result.stdout:
                    print(result.stdout)
                if not success and result.stderr:
                    print(result.stderr)

            self.results[name] = "PASSED" if success else "FAILED"
            return success

        except Exception as e:
            print(f"❌ Error running {name}: {e}")
            self.results[name] = "ERROR"
            return False

    def run_all_tests(self):
        """Run all test suites"""
        print("\n" + "="*70)
        print("🚀 Silver Tier - Master Test Runner")
        print("="*70)
        print(f"Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)

        # Phase 1: Environment Verification
        print("\n📋 Phase 1: Environment Verification")
        print("-"*70)
        self.run_command(
            "Environment Setup",
            [sys.executable, "tests/verify_setup.py"]
        )

        # Phase 2: Unit Tests
        print("\n📋 Phase 2: Unit Tests (Individual Skills)")
        print("-"*70)

        verbose_flag = ["--verbose"] if self.verbose else []

        self.run_command(
            "All Skills Unit Tests",
            [sys.executable, "tests/test_all_skills.py"] + verbose_flag
        )

        # Phase 3: Integration Tests (unless quick mode)
        if not self.quick:
            print("\n📋 Phase 3: Integration Tests (Complete Workflows)")
            print("-"*70)

            self.run_command(
                "Integration Tests",
                [sys.executable, "tests/test_integration.py"]
            )
        else:
            print("\n⏭️  Skipping integration tests (quick mode)")
            self.results["Integration Tests"] = "SKIPPED"

        # Print final summary
        self.print_summary()

    def print_summary(self):
        """Print final test summary"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        print("\n" + "="*70)
        print("📊 Final Test Summary")
        print("="*70 + "\n")

        for name, status in self.results.items():
            icon = {
                "PASSED": "✅",
                "FAILED": "❌",
                "ERROR": "💥",
                "SKIPPED": "⏭️ "
            }.get(status, "❓")
            print(f"{icon} {name}: {status}")

        passed = sum(1 for s in self.results.values() if s == "PASSED")
        failed = sum(1 for s in self.results.values() if s == "FAILED")
        errors = sum(1 for s in self.results.values() if s == "ERROR")
        skipped = sum(1 for s in self.results.values() if s == "SKIPPED")
        total = len(self.results)

        print(f"\n{'='*70}")
        print(f"🎯 Results: {passed} passed, {failed} failed, {errors} errors, {skipped} skipped")
        print(f"⏱️  Duration: {duration:.1f} seconds")
        print(f"{'='*70}\n")

        if failed == 0 and errors == 0:
            print("🎉 All tests passed! Your Silver tier setup is ready.")
            print("\nNext steps:")
            print("  1. Start implementing Phase 1 skills (Gmail)")
            print("  2. Test each skill as you build it")
            print("  3. Run integration tests after completing workflows")
            print()
        else:
            print("⚠️  Some tests failed. Please review the output above.")
            print("\nTroubleshooting:")
            print("  • Check environment setup: python tests/verify_setup.py")
            print("  • Run specific test: python tests/test_all_skills.py --skill gmail")
            print("  • Enable verbose mode: python tests/run_all_tests.py --verbose")
            print()

        return failed == 0 and errors == 0


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Master test runner for Silver tier'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed output from all tests'
    )
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Skip integration tests (faster)'
    )

    args = parser.parse_args()

    runner = TestRunner(verbose=args.verbose, quick=args.quick)
    success = runner.run_all_tests()

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
