"""
instagram_publisher.py — Instagram automation using instagrapi
Works with username + password, no Meta Developer API needed
"""
import time
import os
from pathlib import Path
from typing import List, Optional
from config import settings
from database import update_post_status, add_log

try:
    from instagrapi import Client
    from instagrapi.exceptions import LoginRequired, ChallengeRequired, TwoFactorRequired
    INSTAGRAPI_AVAILABLE = True
except ImportError:
    INSTAGRAPI_AVAILABLE = False
    print("[Instagram] instagrapi not installed. Run: pip install instagrapi")


class InstagramPublisher:
    def __init__(self):
        self.client: Optional[object] = None
        self.logged_in = False
        self.session_file = settings.SESSION_DIR / "instagram_session.json"

    def login(self) -> bool:
        """Login to Instagram with username/password"""
        if not INSTAGRAPI_AVAILABLE:
            print("[Instagram] instagrapi not available")
            return False

        if not settings.INSTAGRAM_USERNAME or not settings.INSTAGRAM_PASSWORD:
            print("[Instagram] No credentials configured")
            return False

        self.client = Client()
        self.client.delay_range = [2, 5]  # Human-like delays

        # Try session reuse first
        if self.session_file.exists():
            try:
                self.client.load_settings(str(self.session_file))
                self.client.login(settings.INSTAGRAM_USERNAME, settings.INSTAGRAM_PASSWORD)
                self.client.get_timeline_feed()  # Test the session
                self.logged_in = True
                print("[Instagram] Logged in using saved session")
                return True
            except Exception:
                print("[Instagram] Saved session expired, logging in fresh...")

        # Fresh login
        try:
            self.client.login(settings.INSTAGRAM_USERNAME, settings.INSTAGRAM_PASSWORD)
            self.client.dump_settings(str(self.session_file))
            self.logged_in = True
            print(f"[Instagram] Successfully logged in as @{settings.INSTAGRAM_USERNAME}")
            return True
        except TwoFactorRequired:
            print("[Instagram] 2FA required — please disable 2FA or handle manually")
            return False
        except ChallengeRequired:
            print("[Instagram] Challenge required — Instagram needs verification")
            return False
        except Exception as e:
            print(f"[Instagram] Login failed: {e}")
            return False

    def publish_carousel(self, image_paths: List[str], caption: str,
                         post_id: int, run_date: str) -> Optional[str]:
        """
        Publish a carousel post to Instagram.
        Returns the Instagram media ID if successful.
        """
        if not self.logged_in:
            if not self.login():
                add_log(run_date, "publish", "Instagram login failed", "error")
                update_post_status(post_id, "failed")
                return None

        # Validate image paths
        valid_paths = []
        for p in image_paths:
            path = Path(p)
            if path.exists():
                valid_paths.append(str(path))
            else:
                print(f"[Instagram] Image not found: {p}")

        if len(valid_paths) < 2:
            add_log(run_date, "publish", f"Not enough images: {len(valid_paths)}", "error")
            update_post_status(post_id, "failed")
            return None

        try:
            add_log(run_date, "publish", f"Uploading {len(valid_paths)} slides to Instagram...", "info")
            update_post_status(post_id, "publishing")

            # Upload carousel
            media = self.client.album_upload(
                paths=valid_paths,
                caption=caption
            )

            instagram_id = str(media.pk)
            update_post_status(post_id, "published", instagram_id)
            add_log(run_date, "publish", f"✓ Published! Instagram ID: {instagram_id}", "success")
            print(f"[Instagram] Published carousel! ID: {instagram_id}")
            return instagram_id

        except Exception as e:
            error_msg = str(e)
            print(f"[Instagram] Upload failed: {error_msg}")
            add_log(run_date, "publish", f"Upload failed: {error_msg}", "error")
            update_post_status(post_id, "failed")

            # Try re-login on auth errors
            if "login" in error_msg.lower() or "auth" in error_msg.lower():
                self.logged_in = False
                if self.session_file.exists():
                    self.session_file.unlink()
            return None

    def test_connection(self) -> dict:
        """Test Instagram connection and return account info"""
        if not INSTAGRAPI_AVAILABLE:
            return {"success": False, "error": "instagrapi not installed"}

        if not settings.INSTAGRAM_USERNAME or not settings.INSTAGRAM_PASSWORD:
            return {"success": False, "error": "No credentials configured"}

        if self.login():
            try:
                user_info = self.client.account_info()
                return {
                    "success": True,
                    "username": user_info.username,
                    "full_name": user_info.full_name,
                    "followers": user_info.follower_count,
                    "following": user_info.following_count,
                    "posts": user_info.media_count,
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        return {"success": False, "error": "Login failed"}

    def fetch_recent_analytics(self, instagram_post_id: str) -> dict:
        """Fetch engagement metrics for a published post"""
        if not self.logged_in:
            self.login()

        try:
            media_info = self.client.media_info(int(instagram_post_id))
            return {
                "likes": media_info.like_count or 0,
                "comments": media_info.comment_count or 0,
                "shares": 0,
                "saves": 0,
                "reach": 0,
                "impressions": 0,
            }
        except Exception as e:
            print(f"[Instagram] Analytics fetch failed: {e}")
            return {}


# Singleton publisher instance
publisher = InstagramPublisher()
