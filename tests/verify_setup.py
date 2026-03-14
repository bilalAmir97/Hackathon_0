#!/usr/bin/env python3
"""
Environment Setup Verification

Quick check to verify your environment is ready for Silver tier development.

Usage:
    python tests/verify_setup.py
    python tests/verify_setup.py --fix  # Attempt to fix issues
"""

import sys
import subprocess
import platform
from pathlib import Path
from typing import List, Tuple


class SetupVerifier:
    """Verify development environment setup"""

    def __init__(self, fix_issues: bool = False):
        self.fix_issues = fix_issues
        self.issues = []
        self.warnings = []
        self.passed = []

    def check(self, name: str, func) -> bool:
        """Run a check and record result"""
        try:
            result, message = func()
            if result:
                self.passed.append(f"✅ {name}")
                return True
            else:
                self.issues.append(f"❌ {name}: {message}")
                return False
        except Exception as e:
            self.issues.append(f"❌ {name}: {str(e)}")
            return False

    def warn(self, name: str, message: str):
        """Record a warning"""
        self.warnings.append(f"⚠️  {name}: {message}")

    def check_python_version(self) -> Tuple[bool, str]:
        """Check Python version >= 3.10"""
        version = sys.version_info
        if version.major >= 3 and version.minor >= 10:
            return True, f"Python {version.major}.{version.minor}.{version.micro}"
        return False, f"Python 3.10+ required, found {version.major}.{version.minor}"

    def check_node_version(self) -> Tuple[bool, str]:
        """Check Node.js version >= 18"""
        try:
            result = subprocess.run(['node', '--version'], capture_output=True, text=True)
            version = result.stdout.strip()
            major = int(version.split('.')[0].replace('v', ''))
            if major >= 18:
                return True, version
            return False, f"Node.js 18+ required, found {version}"
        except FileNotFoundError:
            return False, "Node.js not installed"

    def check_claude_code(self) -> Tuple[bool, str]:
        """Check if Claude Code is installed"""
        try:
            result = subprocess.run(['claude', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                return True, result.stdout.strip()
            return False, "Claude Code not responding"
        except FileNotFoundError:
            return False, "Claude Code not installed"

    def check_pip_packages(self) -> Tuple[bool, str]:
        """Check required pip packages"""
        required = [
            'google-auth',
            'google-auth-oauthlib',
            'google-api-python-client',
            'playwright',
            'watchdog'
        ]

        missing = []
        for package in required:
            try:
                __import__(package.replace('-', '_'))
            except ImportError:
                missing.append(package)

        if missing:
            return False, f"Missing packages: {', '.join(missing)}"
        return True, "All required packages installed"

    def check_playwright_browsers(self) -> Tuple[bool, str]:
        """Check if Playwright browsers are installed"""
        try:
            import playwright
            # Check if chromium is installed
            # This is a simplified check
            return True, "Playwright installed (run 'playwright install' if needed)"
        except ImportError:
            return False, "Playwright not installed"

    def check_pm2(self) -> Tuple[bool, str]:
        """Check if PM2 is installed"""
        try:
            result = subprocess.run(['pm2', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                return True, result.stdout.strip()
            return False, "PM2 not responding"
        except FileNotFoundError:
            return False, "PM2 not installed (npm install -g pm2)"

    def check_vault_structure(self) -> Tuple[bool, str]:
        """Check if vault has correct structure"""
        vault_path = Path('./AI_Employee_Vault')

        if not vault_path.exists():
            return False, "Vault directory not found"

        required_dirs = [
            'Inbox', 'Needs_Action', 'Done', 'Plans', 'Logs',
            'Pending_Approval', 'Approved', 'Rejected'
        ]

        missing = [d for d in required_dirs if not (vault_path / d).exists()]

        if missing:
            return False, f"Missing directories: {', '.join(missing)}"
        return True, "All required directories exist"

    def check_company_handbook(self) -> Tuple[bool, str]:
        """Check if Company Handbook exists"""
        handbook = Path('./AI_Employee_Vault/Company_Handbook.md')
        if handbook.exists():
            return True, "Company Handbook found"
        return False, "Company_Handbook.md not found"

    def check_credentials(self) -> Tuple[bool, str]:
        """Check if credentials files exist"""
        creds = Path('./credentials.json')
        if creds.exists():
            return True, "Gmail credentials found"
        return False, "credentials.json not found (optional for testing)"

    def check_env_file(self) -> Tuple[bool, str]:
        """Check if .env file exists"""
        env_file = Path('./.env')
        if env_file.exists():
            return True, ".env file found"
        return False, ".env file not found (copy from .env.example)"

    def check_skills_directory(self) -> Tuple[bool, str]:
        """Check if skills directory exists"""
        skills_dir = Path('./.claude/skills')
        if not skills_dir.exists():
            return False, "Skills directory not found"

        skill_dirs = [
            'monitor-gmail', 'send-email', 'process-emails',
            'approve-actions', 'monitor-whatsapp', 'post-linkedin',
            'schedule-tasks', 'reasoning-loop'
        ]

        existing = [d for d in skill_dirs if (skills_dir / d / 'SKILL.md').exists()]

        if len(existing) == len(skill_dirs):
            return True, f"All {len(skill_dirs)} skills found"
        return False, f"Only {len(existing)}/{len(skill_dirs)} skills found"

    def check_scripts_directory(self) -> Tuple[bool, str]:
        """Check if scripts directory exists"""
        scripts_dir = Path('./scripts')
        if not scripts_dir.exists():
            return False, "Scripts directory not found"

        required_scripts = ['orchestrator.py']
        missing = [s for s in required_scripts if not (scripts_dir / s).exists()]

        if missing:
            return False, f"Missing scripts: {', '.join(missing)}"
        return True, "All required scripts found"

    def run_all_checks(self):
        """Run all verification checks"""
        print("\n" + "="*70)
        print("🔍 Silver Tier Environment Verification")
        print("="*70 + "\n")

        print("📦 Checking Dependencies...")
        print("-"*70)
        self.check("Python 3.10+", self.check_python_version)
        self.check("Node.js 18+", self.check_node_version)
        self.check("Claude Code", self.check_claude_code)
        self.check("Python Packages", self.check_pip_packages)
        self.check("Playwright Browsers", self.check_playwright_browsers)
        self.check("PM2 Process Manager", self.check_pm2)

        print("\n📁 Checking Project Structure...")
        print("-"*70)
        self.check("Vault Structure", self.check_vault_structure)
        self.check("Company Handbook", self.check_company_handbook)
        self.check("Skills Directory", self.check_skills_directory)
        self.check("Scripts Directory", self.check_scripts_directory)

        print("\n🔐 Checking Configuration...")
        print("-"*70)
        self.check("Environment File", self.check_env_file)
        self.check("Gmail Credentials", self.check_credentials)

        # Print results
        print("\n" + "="*70)
        print("📊 Verification Results")
        print("="*70 + "\n")

        if self.passed:
            print("✅ Passed Checks:")
            for item in self.passed:
                print(f"  {item}")

        if self.warnings:
            print("\n⚠️  Warnings:")
            for item in self.warnings:
                print(f"  {item}")

        if self.issues:
            print("\n❌ Issues Found:")
            for item in self.issues:
                print(f"  {item}")

        print("\n" + "="*70)

        total = len(self.passed) + len(self.issues)
        success_rate = (len(self.passed) / total * 100) if total > 0 else 0

        print(f"🎯 Overall: {len(self.passed)}/{total} checks passed ({success_rate:.1f}%)")
        print("="*70 + "\n")

        if self.issues:
            print("💡 Next Steps:")
            print("-"*70)

            if any("Python" in issue for issue in self.issues):
                print("  • Install Python 3.10+: https://www.python.org/downloads/")

            if any("Node.js" in issue for issue in self.issues):
                print("  • Install Node.js 18+: https://nodejs.org/")

            if any("Claude Code" in issue for issue in self.issues):
                print("  • Install Claude Code: https://claude.com/product/claude-code")

            if any("packages" in issue for issue in self.issues):
                print("  • Install Python packages: pip install -r requirements.txt")

            if any("PM2" in issue for issue in self.issues):
                print("  • Install PM2: npm install -g pm2")

            if any("Vault" in issue for issue in self.issues):
                print("  • Create vault structure: python scripts/setup_vault.py")

            if any("Skills" in issue for issue in self.issues):
                print("  • Skills already created in .claude/skills/")

            if any(".env" in issue for issue in self.issues):
                print("  • Copy .env.example to .env and configure")

            if any("credentials" in issue for issue in self.issues):
                print("  • Optional: Set up Gmail API credentials for email features")

            print()

        return len(self.issues) == 0


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Verify Silver tier development environment'
    )
    parser.add_argument(
        '--fix',
        action='store_true',
        help='Attempt to fix issues automatically (not implemented yet)'
    )

    args = parser.parse_args()

    verifier = SetupVerifier(fix_issues=args.fix)
    success = verifier.run_all_checks()

    if success:
        print("🎉 Your environment is ready for Silver tier development!")
        print("\nNext steps:")
        print("  1. Review the skills in .claude/skills/")
        print("  2. Run tests: python tests/test_all_skills.py")
        print("  3. Start with Phase 1: Gmail setup")
        print()
    else:
        print("⚠️  Please fix the issues above before proceeding.")
        print()

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
