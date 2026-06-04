"""
instagram_publisher.py — Instagram automation using instagrapi
Works with username + password, no Meta Developer API needed
"""
import time
import os
import requests
import tempfile
from pathlib import Path
from typing import List, Optional
from config import settings
from database import update_post_status, add_log

try:
    # pyrefly: ignore [missing-import]
    from instagrapi import Client
    # pyrefly: ignore [missing-import]
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
        self.client.delay_range = [2, 5]

        if self.session_file.exists():
            try:
                self.client.load_settings(str(self.session_file))
                self.client.login(settings.INSTAGRAM_USERNAME, settings.INSTAGRAM_PASSWORD)
                self.client.get_timeline_feed()
                self.logged_in = True
                print("[Instagram] Logged in using saved session")
                return True
            except Exception:
                print("[Instagram] Saved session expired, logging in fresh...")

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
        if not self.logged_in:
            if not self.login():
                add_log(run_date, "publish", "Instagram login failed", "error")
                update_post_status(post_id, "failed")
                return None

        # image_paths are now Cloudinary URLs (or local fallbacks)
        temp_dir = Path(tempfile.gettempdir()) / "antigravity_ig_upload"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        valid_paths = []
        for i, url_or_path in enumerate(image_paths):
            if url_or_path.startswith("http"):
                # Download Cloudinary image to temp file
                try:
                    res = requests.get(url_or_path, stream=True)
                    res.raise_for_status()
                    tmp_file = temp_dir / f"slide_{post_id}_{i}.png"
                    with open(tmp_file, "wb") as f:
                        for chunk in res.iter_content(chunk_size=8192):
                            f.write(chunk)
                    valid_paths.append(str(tmp_file))
                except Exception as e:
                    print(f"Failed to download image {url_or_path}: {e}")
            else:
                path = Path(url_or_path)
                if path.exists():
                    valid_paths.append(str(path))

        if len(valid_paths) < 2:
            add_log(run_date, "publish", f"Not enough images: {len(valid_paths)}", "error")
            update_post_status(post_id, "failed")
            return None

        try:
            add_log(run_date, "publish", f"Uploading {len(valid_paths)} slides to Instagram...", "info")
            update_post_status(post_id, "publishing")

            media = self.client.album_upload(
                paths=valid_paths,
                caption=caption
            )
            media_id = media.dict().get("id")
            
            update_post_status(post_id, "published", instagram_post_id=media_id)
            return media_id

        except Exception as e:
            import traceback
            add_log(run_date, "publish", f"Upload failed: {e}", "error")
            print(traceback.format_exc())
            update_post_status(post_id, "failed")
            return None
        finally:
            # Cleanup temp files
            for p in valid_paths:
                try:
                    if "antigravity_ig_upload" in p:
                        os.remove(p)
                except Exception:
                    pass

    def test_connection(self):
        if not self.logged_in:
            if not self.login():
                return {"status": "error", "message": "Login failed"}
        return {"status": "success", "message": f"Connected as @{settings.INSTAGRAM_USERNAME}"}


publisher = InstagramPublisher()
