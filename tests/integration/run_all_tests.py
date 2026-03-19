"""
Integration Test Runner

Runs all cross-domain integration tests and provides comprehensive results.

Tests:
1. Email → Invoice → Payment workflow
2. Project → Social Posts workflow
3. Weekly Audit aggregation workflow

Usage:
    python tests/integration/run_all_tests.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.integration.test_email_to_invoice_workflow import EmailToInvoiceWorkflowTest
from tests.integration.test_project_to_social_workflow import ProjectToSocialPostsWorkflowTest
from tests.integration.test_weekly_audit_workflow import WeeklyAuditWorkflowTest


def main():
    """Run all integration tests."""
    print("\n")
    print("=" * 70)
    print("AI EMPLOYEE SYSTEM - INTEGRATION TEST SUITE")
    print("=" * 70)
    print("\nRunning cross-domain workflow tests...\n")

    results = []

    # Test 1: Email to Invoice workflow
    print("\n" + "=" * 70)
    test1 = EmailToInvoiceWorkflowTest()
    success1 = test1.run_test()
    results.append(('Email → Invoice → Payment', success1))

    # Test 2: Project to Social Posts workflow
    print("\n" + "=" * 70)
    test2 = ProjectToSocialPostsWorkflowTest()
    success2 = test2.run_test()
    results.append(('Project → Social Posts', success2))

    # Test 3: Weekly Audit workflow
    print("\n" + "=" * 70)
    test3 = WeeklyAuditWorkflowTest()
    success3 = test3.run_test()
    results.append(('Weekly Audit Aggregation', success3))

    # Print overall summary
    print("\n" + "=" * 70)
    print("OVERALL TEST RESULTS")
    print("=" * 70)
    print()

    for workflow, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {workflow}")

    print()
    passed = sum(1 for _, success in results if success)
    total = len(results)
    print(f"Total: {passed}/{total} workflows passed")
    print()

    if passed == total:
        print("✅ All integration tests passed!")
        print("\nThe AI Employee system is fully integrated and operational.")
        return 0
    else:
        print(f"❌ {total - passed} workflow(s) failed")
        print("\nSome integrations need attention. Review the test output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
