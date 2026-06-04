"""
instagram_publisher.py — Instagram automation using Meta Graph API
"""
import time
import requests
from typing import List, Optional
from config import settings
from database import update_post_status, add_log

class InstagramPublisher:
    def __init__(self):
        self.base_url = "https://graph.facebook.com/v19.0"

    def is_configured(self) -> bool:
        return bool(settings.META_ACCESS_TOKEN and settings.INSTAGRAM_ACCOUNT_ID)

    def test_connection(self):
        if not self.is_configured():
            return {"status": "error", "message": "Graph API credentials not configured"}
        
        try:
            url = f"{self.base_url}/{settings.INSTAGRAM_ACCOUNT_ID}"
            params = {
                "fields": "username,followers_count,media_count",
                "access_token": settings.META_ACCESS_TOKEN
            }
            res = requests.get(url, params=params)
            res.raise_for_status()
            data = res.json()
            
            return {
                "success": True, 
                "username": data.get("username", "Unknown"),
                "followers": data.get("followers_count", 0),
                "posts": data.get("media_count", 0),
                "message": f"Connected to @{data.get('username')}"
            }
        except Exception as e:
            err_msg = str(e)
            if hasattr(e, "response") and getattr(e, "response") is not None:
                err_msg = e.response.text
            return {"success": False, "error": f"Graph API Error: {err_msg}"}

    def _upload_carousel_item(self, image_url: str) -> Optional[str]:
        """Uploads a single image as a carousel item container"""
        url = f"{self.base_url}/{settings.INSTAGRAM_ACCOUNT_ID}/media"
        payload = {
            "image_url": image_url,
            "is_carousel_item": "true",
            "access_token": settings.META_ACCESS_TOKEN
        }
        res = requests.post(url, data=payload)
        res.raise_for_status()
        return res.json().get("id")

    def publish_carousel(self, image_urls: List[str], caption: str,
                         post_id: int, run_date: str) -> Optional[str]:
        if not self.is_configured():
            add_log(run_date, "publish", "Graph API not configured", "error")
            update_post_status(post_id, "failed")
            return None

        # Filter out local paths, Graph API requires public URLs
        public_urls = [url for url in image_urls if url.startswith("http")]
        
        if len(public_urls) < 2:
            add_log(run_date, "publish", f"Not enough public image URLs: {len(public_urls)}", "error")
            update_post_status(post_id, "failed")
            return None

        try:
            add_log(run_date, "publish", f"Uploading {len(public_urls)} slides to Instagram Graph API...", "info")
            update_post_status(post_id, "publishing")

            # 1. Create containers for each carousel item
            item_ids = []
            for img_url in public_urls:
                item_id = self._upload_carousel_item(img_url)
                if item_id:
                    item_ids.append(item_id)
                time.sleep(1) # Rate limit protection

            if len(item_ids) != len(public_urls):
                raise Exception("Failed to create all carousel item containers")

            # 2. Create the carousel container
            carousel_url = f"{self.base_url}/{settings.INSTAGRAM_ACCOUNT_ID}/media"
            carousel_payload = {
                "media_type": "CAROUSEL",
                "caption": caption,
                "children": ",".join(item_ids),
                "access_token": settings.META_ACCESS_TOKEN
            }
            res = requests.post(carousel_url, data=carousel_payload)
            res.raise_for_status()
            carousel_container_id = res.json().get("id")

            # 3. Publish the carousel
            publish_url = f"{self.base_url}/{settings.INSTAGRAM_ACCOUNT_ID}/media_publish"
            publish_payload = {
                "creation_id": carousel_container_id,
                "access_token": settings.META_ACCESS_TOKEN
            }
            res = requests.post(publish_url, data=publish_payload)
            res.raise_for_status()
            published_id = res.json().get("id")

            update_post_status(post_id, "published", instagram_post_id=published_id)
            return published_id

        except Exception as e:
            import traceback
            err_msg = str(e)
            if hasattr(e, "response") and getattr(e, "response") is not None:
                err_msg = e.response.text
            
            add_log(run_date, "publish", f"Upload failed: {err_msg}", "error")
            print(traceback.format_exc())
            update_post_status(post_id, "failed")
            return None

publisher = InstagramPublisher()

