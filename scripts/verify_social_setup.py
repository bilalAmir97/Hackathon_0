#!/usr/bin/env python3
"""
Verify Facebook & Instagram MCP Server Setup

This script validates your Meta API credentials and checks if everything is configured correctly.
Run this before using the MCP server to catch configuration issues early.

Usage:
    python scripts/verify_social_setup.py
"""

import os
import sys
import requests
from pathlib import Path
from typing import Dict, List, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}\n")


def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.END}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")


def print_info(text: str):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")


def check_env_variables() -> Tuple[bool, List[str]]:
    """Check if all required environment variables are set"""
    print_header("Checking Environment Variables")

    required_vars = [
        "FACEBOOK_PAGE_ACCESS_TOKEN",
        "FACEBOOK_PAGE_ID",
        "INSTAGRAM_BUSINESS_ACCESS_TOKEN",
        "INSTAGRAM_BUSINESS_ACCOUNT_ID",
    ]

    missing_vars = []

    for var in required_vars:
        value = os.getenv(var)
        if not value:
            print_error(f"{var} is not set")
            missing_vars.append(var)
        else:
            # Mask token for security
            if "TOKEN" in var:
                masked = value[:10] + "..." + value[-10:] if len(value) > 20 else "***"
                print_success(f"{var} = {masked}")
            else:
                print_success(f"{var} = {value}")

    if missing_vars:
        print_error(f"\nMissing {len(missing_vars)} required environment variable(s)")
        return False, missing_vars

    print_success("\nAll required environment variables are set")
    return True, []


def validate_facebook_token() -> Tuple[bool, Dict]:
    """Validate Facebook Page access token"""
    print_header("Validating Facebook Token")

    token = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")
    page_id = os.getenv("FACEBOOK_PAGE_ID")
    api_version = os.getenv("META_GRAPH_API_VERSION", "v19.0")

    try:
        # Test token by fetching page info
        url = f"https://graph.facebook.com/{api_version}/{page_id}"
        params = {
            "access_token": token,
            "fields": "id,name,category,fan_count,access_token"
        }

        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            print_success(f"Token is valid!")
            print_info(f"Page Name: {data.get('name', 'N/A')}")
            print_info(f"Page ID: {data.get('id', 'N/A')}")
            print_info(f"Category: {data.get('category', 'N/A')}")
            print_info(f"Followers: {data.get('fan_count', 'N/A')}")
            return True, data
        else:
            error_data = response.json()
            print_error(f"Token validation failed: {error_data.get('error', {}).get('message', 'Unknown error')}")
            return False, error_data

    except requests.exceptions.RequestException as e:
        print_error(f"Network error: {str(e)}")
        return False, {}


def validate_instagram_token() -> Tuple[bool, Dict]:
    """Validate Instagram Business Account access token"""
    print_header("Validating Instagram Token")

    token = os.getenv("INSTAGRAM_BUSINESS_ACCESS_TOKEN")
    account_id = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID")
    api_version = os.getenv("META_GRAPH_API_VERSION", "v19.0")

    try:
        # Test token by fetching account info
        url = f"https://graph.facebook.com/{api_version}/{account_id}"
        params = {
            "access_token": token,
            "fields": "id,username,name,profile_picture_url,followers_count,media_count"
        }

        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            print_success(f"Token is valid!")
            print_info(f"Username: @{data.get('username', 'N/A')}")
            print_info(f"Account ID: {data.get('id', 'N/A')}")
            print_info(f"Name: {data.get('name', 'N/A')}")
            print_info(f"Followers: {data.get('followers_count', 'N/A')}")
            print_info(f"Posts: {data.get('media_count', 'N/A')}")
            return True, data
        else:
            error_data = response.json()
            print_error(f"Token validation failed: {error_data.get('error', {}).get('message', 'Unknown error')}")
            return False, error_data

    except requests.exceptions.RequestException as e:
        print_error(f"Network error: {str(e)}")
        return False, {}


def check_permissions() -> Tuple[bool, List[str]]:
    """Check if tokens have required permissions"""
    print_header("Checking Token Permissions")

    token = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")
    api_version = os.getenv("META_GRAPH_API_VERSION", "v19.0")

    try:
        # Debug token to check permissions
        url = f"https://graph.facebook.com/{api_version}/debug_token"
        params = {
            "input_token": token,
            "access_token": token
        }

        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json().get("data", {})
            scopes = data.get("scopes", [])

            required_permissions = [
                "pages_manage_posts",
                "pages_read_engagement",
                "pages_show_list",
                "instagram_basic",
                "instagram_content_publish",
                "instagram_manage_insights"
            ]

            missing_permissions = []

            for perm in required_permissions:
                if perm in scopes:
                    print_success(f"{perm}")
                else:
                    print_warning(f"{perm} (missing)")
                    missing_permissions.append(perm)

            if missing_permissions:
                print_warning(f"\nMissing {len(missing_permissions)} permission(s)")
                print_info("You may not be able to use all features")
                return False, missing_permissions

            print_success("\nAll required permissions are granted")
            return True, []
        else:
            print_error("Could not check permissions")
            return False, []

    except requests.exceptions.RequestException as e:
        print_error(f"Network error: {str(e)}")
        return False, []


def main():
    """Main verification flow"""
    print_header("Facebook & Instagram MCP Server Setup Verification")

    results = {
        "env_vars": False,
        "facebook_token": False,
        "instagram_token": False,
        "permissions": False
    }

    # Step 1: Check environment variables
    results["env_vars"], missing_vars = check_env_variables()

    if not results["env_vars"]:
        print_error("\n❌ Setup incomplete: Missing environment variables")
        print_info("\nPlease configure the following in your .env file:")
        for var in missing_vars:
            print(f"  - {var}")
        print_info("\nSee QUICK_SETUP.md for instructions")
        sys.exit(1)

    # Step 2: Validate Facebook token
    results["facebook_token"], _ = validate_facebook_token()

    # Step 3: Validate Instagram token
    results["instagram_token"], _ = validate_instagram_token()

    # Step 4: Check permissions
    results["permissions"], missing_perms = check_permissions()

    # Final summary
    print_header("Verification Summary")

    all_passed = all(results.values())

    if all_passed:
        print_success("✅ All checks passed!")
        print_success("Your Facebook & Instagram MCP Server is ready to use")
        print_info("\nNext steps:")
        print("  1. Install dependencies: uv pip install requests Pillow cachetools")
        print("  2. Run tests: pytest tests/test_*social*.py -v")
        print("  3. Start using the MCP server via Claude Code")
    else:
        print_warning("⚠️  Some checks failed")

        if not results["facebook_token"]:
            print_error("  - Facebook token is invalid")
        if not results["instagram_token"]:
            print_error("  - Instagram token is invalid")
        if not results["permissions"]:
            print_warning("  - Some permissions are missing")

        print_info("\nSee QUICK_SETUP.md for setup instructions")
        sys.exit(1)


if __name__ == "__main__":
    main()
