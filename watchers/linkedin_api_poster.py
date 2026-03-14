#!/usr/bin/env python3
"""
LinkedIn API Poster (Official API)

Uses LinkedIn's official API for posting instead of browser automation.
More reliable and compliant with LinkedIn's ToS.
"""

import sys
import json
import time
import logging
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import requests

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()


class LinkedInAPIAuth:
    """Handle LinkedIn OAuth 2.0 authentication."""

    def __init__(self):
        self.client_id = os.getenv('LINKEDIN_CLIENT_ID')
        self.client_secret = os.getenv('LINKEDIN_CLIENT_SECRET')
        self.redirect_uri = os.getenv('LINKEDIN_REDIRECT_URI', 'http://localhost:8001/callback')

        if not self.client_id or not self.client_secret:
            raise ValueError("LinkedIn API credentials not found in .env file")

        self.auth_code = None
        self.access_token = None

    def get_authorization_url(self) -> str:
        """Generate LinkedIn OAuth authorization URL."""
        scope = 'openid profile email w_member_social'
        auth_url = (
            f"https://www.linkedin.com/oauth/v2/authorization?"
            f"response_type=code&"
            f"client_id={self.client_id}&"
            f"redirect_uri={self.redirect_uri}&"
            f"scope={scope}"
        )
        return auth_url

    def exchange_code_for_token(self, auth_code: str) -> str:
        """Exchange authorization code for access token."""
        token_url = "https://www.linkedin.com/oauth/v2/accessToken"

        data = {
            'grant_type': 'authorization_code',
            'code': auth_code,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri': self.redirect_uri
        }

        response = requests.post(token_url, data=data)
        response.raise_for_status()

        token_data = response.json()
        return token_data['access_token']

    def get_user_info(self, access_token: str) -> Dict:
        """Get LinkedIn user profile information."""
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get('https://api.linkedin.com/v2/userinfo', headers=headers)
        response.raise_for_status()
        return response.json()


class CallbackHandler(BaseHTTPRequestHandler):
    """HTTP server to handle OAuth callback."""

    auth_code = None

    def do_GET(self):
        """Handle GET request with authorization code."""
        query = urlparse(self.path).query
        params = parse_qs(query)

        if 'code' in params:
            CallbackHandler.auth_code = params['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"""
                <html><body>
                <h1>Authorization Successful!</h1>
                <p>You can close this window and return to the terminal.</p>
                </body></html>
            """)
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<html><body><h1>Authorization Failed</h1></body></html>")

    def log_message(self, format, *args):
        """Suppress server logs."""
        pass


class LinkedInAPIPoster:
    """Post to LinkedIn using official API."""

    def __init__(self, vault_path: str = "AI_Employee_Vault"):
        self.vault_path = Path(vault_path)
        self.pending_folder = self.vault_path / "Pending_LinkedIn"
        self.approved_folder = self.vault_path / "Approved_LinkedIn"
        self.posted_folder = self.vault_path / "Posted_LinkedIn"
        self.state_folder = self.vault_path / ".state"
        self.token_file = self.state_folder / "linkedin_api_token.json"

        # Create folders
        self.pending_folder.mkdir(exist_ok=True)
        self.approved_folder.mkdir(exist_ok=True)
        self.posted_folder.mkdir(exist_ok=True)
        self.state_folder.mkdir(exist_ok=True)

        # Setup logging
        log_file = self.vault_path / "Logs" / f"linkedin_api_{datetime.now().strftime('%Y%m%d')}.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

        self.auth = LinkedInAPIAuth()
        self.access_token = None
        self.user_id = None

    def load_token(self) -> bool:
        """Load saved access token."""
        if self.token_file.exists():
            try:
                with open(self.token_file) as f:
                    data = json.load(f)
                    self.access_token = data.get('access_token')
                    self.user_id = data.get('user_id')
                    self.logger.info("✓ Loaded saved LinkedIn API token")
                    return True
            except Exception as e:
                self.logger.error(f"Failed to load token: {e}")
        return False

    def save_token(self, access_token: str, user_id: str):
        """Save access token."""
        try:
            with open(self.token_file, 'w') as f:
                json.dump({
                    'access_token': access_token,
                    'user_id': user_id,
                    'saved_at': datetime.now().isoformat()
                }, f, indent=2)
            self.logger.info("✓ Saved LinkedIn API token")
        except Exception as e:
            self.logger.error(f"Failed to save token: {e}")

    def authenticate(self) -> bool:
        """Authenticate with LinkedIn API."""
        # Try loading saved token
        if self.load_token():
            # Verify token is still valid
            try:
                user_info = self.auth.get_user_info(self.access_token)
                self.logger.info(f"✓ Authenticated as: {user_info.get('name')}")
                return True
            except:
                self.logger.warning("Saved token is invalid, re-authenticating...")

        # Need new authentication
        self.logger.info("=" * 60)
        self.logger.info("LinkedIn API Authentication Required")
        self.logger.info("=" * 60)
        self.logger.info("1. Browser will open to LinkedIn authorization page")
        self.logger.info("2. Log in and authorize the app")
        self.logger.info("3. You'll be redirected back automatically")
        self.logger.info("=" * 60)

        # Get authorization URL
        auth_url = self.auth.get_authorization_url()

        # Start local server to receive callback
        server = HTTPServer(('localhost', 8001), CallbackHandler)

        # Open browser
        webbrowser.open(auth_url)
        self.logger.info("⏳ Waiting for authorization...")

        # Wait for callback (timeout after 5 minutes)
        timeout = time.time() + 300
        while not CallbackHandler.auth_code and time.time() < timeout:
            server.handle_request()

        if not CallbackHandler.auth_code:
            self.logger.error("❌ Authorization timeout")
            return False

        # Exchange code for token
        try:
            self.access_token = self.auth.exchange_code_for_token(CallbackHandler.auth_code)
            user_info = self.auth.get_user_info(self.access_token)
            self.user_id = user_info['sub']

            # Save token
            self.save_token(self.access_token, self.user_id)

            self.logger.info(f"✅ Authenticated as: {user_info.get('name')}")
            return True

        except Exception as e:
            self.logger.error(f"❌ Authentication failed: {e}")
            return False

    def upload_image(self, image_path: Path) -> Optional[str]:
        """Upload image to LinkedIn and return asset URN."""
        try:
            self.logger.info(f"📤 Uploading image: {image_path.name}")

            # Step 1: Register upload
            register_url = "https://api.linkedin.com/v2/assets?action=registerUpload"

            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json',
                'X-Restli-Protocol-Version': '2.0.0'
            }

            register_data = {
                "registerUploadRequest": {
                    "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                    "owner": f"urn:li:person:{self.user_id}",
                    "serviceRelationships": [{
                        "relationshipType": "OWNER",
                        "identifier": "urn:li:userGeneratedContent"
                    }]
                }
            }

            response = requests.post(register_url, headers=headers, json=register_data)
            response.raise_for_status()

            result = response.json()
            upload_url = result['value']['uploadMechanism']['com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest']['uploadUrl']
            asset_urn = result['value']['asset']

            self.logger.info(f"✓ Upload registered, asset URN: {asset_urn}")

            # Step 2: Upload image file
            with open(image_path, 'rb') as f:
                upload_headers = {
                    'Authorization': f'Bearer {self.access_token}'
                }
                upload_response = requests.put(upload_url, data=f, headers=upload_headers)
                upload_response.raise_for_status()

            self.logger.info(f"✅ Image uploaded successfully")
            return asset_urn

        except Exception as e:
            self.logger.error(f"Failed to upload image: {e}")
            if hasattr(e, 'response'):
                self.logger.error(f"Response: {e.response.text}")
            return None

    def upload_video(self, video_path: Path) -> Optional[str]:
        """Upload video to LinkedIn and return asset URN."""
        try:
            self.logger.info(f"📤 Uploading video: {video_path.name}")

            # Step 1: Register upload
            register_url = "https://api.linkedin.com/v2/assets?action=registerUpload"

            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json',
                'X-Restli-Protocol-Version': '2.0.0'
            }

            register_data = {
                "registerUploadRequest": {
                    "recipes": ["urn:li:digitalmediaRecipe:feedshare-video"],
                    "owner": f"urn:li:person:{self.user_id}",
                    "serviceRelationships": [{
                        "relationshipType": "OWNER",
                        "identifier": "urn:li:userGeneratedContent"
                    }]
                }
            }

            response = requests.post(register_url, headers=headers, json=register_data)
            response.raise_for_status()

            result = response.json()
            upload_url = result['value']['uploadMechanism']['com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest']['uploadUrl']
            asset_urn = result['value']['asset']

            self.logger.info(f"✓ Upload registered, asset URN: {asset_urn}")

            # Step 2: Upload video file
            with open(video_path, 'rb') as f:
                upload_headers = {
                    'Authorization': f'Bearer {self.access_token}'
                }
                upload_response = requests.put(upload_url, data=f, headers=upload_headers)
                upload_response.raise_for_status()

            self.logger.info(f"✅ Video uploaded successfully")

            # Note: Video processing takes time on LinkedIn's side
            self.logger.info("⏳ Video is processing on LinkedIn (may take a few minutes)")

            return asset_urn

        except Exception as e:
            self.logger.error(f"Failed to upload video: {e}")
            if hasattr(e, 'response'):
                self.logger.error(f"Response: {e.response.text}")
            return None

    def create_post(self, content: str, media_urns: list = None, media_type: str = "NONE") -> Optional[str]:
        """Create a LinkedIn post using API with optional media."""
        try:
            url = "https://api.linkedin.com/v2/ugcPosts"

            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json',
                'X-Restli-Protocol-Version': '2.0.0'
            }

            share_content = {
                "shareCommentary": {
                    "text": content
                },
                "shareMediaCategory": media_type
            }

            # Add media if provided
            if media_urns and media_type != "NONE":
                share_content["media"] = []
                for media_urn in media_urns:
                    share_content["media"].append({
                        "status": "READY",
                        "media": media_urn
                    })

            post_data = {
                "author": f"urn:li:person:{self.user_id}",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": share_content
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }

            response = requests.post(url, headers=headers, json=post_data)
            response.raise_for_status()

            post_id = response.headers.get('X-RestLi-Id')
            self.logger.info(f"✅ Post created successfully! ID: {post_id}")

            return post_id

        except Exception as e:
            self.logger.error(f"Failed to create post: {e}")
            if hasattr(e, 'response'):
                self.logger.error(f"Response: {e.response.text}")
            return None

    def parse_post_file(self, file_path: Path) -> Optional[Dict]:
        """Parse LinkedIn post file with media support."""
        try:
            content = file_path.read_text()

            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter = {}
                    for line in parts[1].strip().split('\n'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            frontmatter[key.strip()] = value.strip()

                    body = parts[2].strip()

                    if '## Content' in body:
                        content_start = body.index('## Content') + len('## Content')
                        content_end = body.find('##', content_start)
                        if content_end == -1:
                            content_end = len(body)

                        post_content = body[content_start:content_end].strip()

                        # Parse media files
                        media_files = []
                        if 'media' in frontmatter:
                            media_value = frontmatter['media']
                            # Support single file or comma-separated list
                            media_paths = [m.strip() for m in media_value.split(',')]
                            for media_path in media_paths:
                                if media_path:
                                    # Resolve relative paths
                                    if not media_path.startswith('/'):
                                        media_path = str(self.vault_path / media_path)
                                    media_files.append(Path(media_path))

                        return {
                            'frontmatter': frontmatter,
                            'content': post_content,
                            'media_files': media_files,
                            'file_path': file_path
                        }

            self.logger.error(f"Invalid post format: {file_path.name}")
            return None

        except Exception as e:
            self.logger.error(f"Failed to parse post file {file_path.name}: {e}")
            return None

    def validate_media_file(self, media_path: Path) -> tuple[bool, str]:
        """Validate media file type and size."""
        if not media_path.exists():
            return False, f"File not found: {media_path}"

        # Check file extension
        ext = media_path.suffix.lower()

        # Image validation
        if ext in ['.jpg', '.jpeg', '.png']:
            size_mb = media_path.stat().st_size / (1024 * 1024)
            if size_mb > 10:
                return False, f"Image too large: {size_mb:.1f}MB (max 10MB)"
            return True, "IMAGE"

        # Video validation
        elif ext in ['.mp4']:
            size_mb = media_path.stat().st_size / (1024 * 1024)
            if size_mb > 200:
                return False, f"Video too large: {size_mb:.1f}MB (max 200MB)"
            return True, "VIDEO"

        else:
            return False, f"Unsupported file type: {ext} (supported: jpg, png, mp4)"

    def process_approved_posts(self):
        """Process all approved posts with media support."""
        approved_posts = sorted(self.approved_folder.glob("*.md"), key=lambda x: x.stat().st_mtime)

        if not approved_posts:
            self.logger.info("No approved posts to process")
            return

        self.logger.info(f"Found {len(approved_posts)} approved post(s)")

        for post_file in approved_posts:
            self.logger.info(f"\n📋 Processing: {post_file.name}")

            post_data = self.parse_post_file(post_file)
            if not post_data:
                continue

            # Handle media uploads if present
            media_urns = []
            media_type = "NONE"

            if post_data['media_files']:
                self.logger.info(f"📎 Found {len(post_data['media_files'])} media file(s)")

                for media_file in post_data['media_files']:
                    # Validate media file
                    valid, result = self.validate_media_file(media_file)

                    if not valid:
                        self.logger.error(f"❌ Media validation failed: {result}")
                        self.create_failure_alert(post_data, f"Media validation failed: {result}")
                        continue

                    media_type = result  # "IMAGE" or "VIDEO"

                    # Upload media
                    if media_type == "IMAGE":
                        media_urn = self.upload_image(media_file)
                    elif media_type == "VIDEO":
                        media_urn = self.upload_video(media_file)
                    else:
                        media_urn = None

                    if media_urn:
                        media_urns.append(media_urn)
                    else:
                        self.logger.error(f"❌ Failed to upload: {media_file.name}")
                        self.create_failure_alert(post_data, f"Media upload failed: {media_file.name}")
                        break

                # If any media upload failed, skip this post
                if len(media_urns) != len(post_data['media_files']):
                    self.logger.error(f"❌ Skipping post due to media upload failures")
                    continue

            # Create post with or without media
            post_id = self.create_post(
                content=post_data['content'],
                media_urns=media_urns if media_urns else None,
                media_type=media_type
            )

            if post_id:
                self.mark_as_posted(post_data, post_id)
                self.logger.info(f"✅ Successfully posted: {post_file.name}")
            else:
                self.create_failure_alert(post_data, "API post creation failed")
                self.logger.error(f"❌ Failed to post: {post_file.name}")

            time.sleep(5)

    def run_once(self):
        """Run one cycle of post processing."""
        self.logger.info("=" * 60)
        self.logger.info("📱 LinkedIn API Poster - Processing Approved Posts")
        self.logger.info("=" * 60)

        if not self.authenticate():
            self.logger.error("❌ Authentication failed")
            return

        self.process_approved_posts()

    def run_continuous(self, check_interval: int = 300):
        """Run continuously."""
        self.logger.info("🔄 Starting continuous LinkedIn API posting")
        self.logger.info(f"Check interval: {check_interval}s")

        try:
            while True:
                self.run_once()
                self.logger.info(f"\n💤 Sleeping for {check_interval}s...")
                time.sleep(check_interval)
        except KeyboardInterrupt:
            self.logger.info("\n⏹️  LinkedIn API poster stopped")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='LinkedIn API Poster')
    parser.add_argument('--vault', default='AI_Employee_Vault', help='Vault path')
    parser.add_argument('--continuous', action='store_true', help='Run continuously')
    parser.add_argument('--interval', type=int, default=300, help='Check interval (seconds)')

    args = parser.parse_args()

    poster = LinkedInAPIPoster(vault_path=args.vault)

    if args.continuous:
        poster.run_continuous(check_interval=args.interval)
    else:
        poster.run_once()


if __name__ == "__main__":
    main()
