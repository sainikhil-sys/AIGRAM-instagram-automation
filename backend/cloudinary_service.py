"""
cloudinary_service.py — Cloudinary storage integration for generated assets
"""
import os
from pathlib import Path
from typing import List, Optional
from config import settings

CLOUDINARY_AVAILABLE = False
try:
    import cloudinary
    import cloudinary.uploader
    CLOUDINARY_AVAILABLE = True
except ImportError:
    pass


class CloudinaryService:
    def __init__(self):
        self.configured = False
        self._initialize()

    def _initialize(self):
        if not CLOUDINARY_AVAILABLE:
            print("[Cloudinary] SDK not installed.")
            return

        # Configure from CLOUDINARY_URL if available
        cloudinary_url = settings.CLOUDINARY_URL or os.getenv("CLOUDINARY_URL")
        if cloudinary_url:
            try:
                cloudinary.config_from_url(cloudinary_url)
                self.configured = True
                print("[Cloudinary] Successfully configured via connection URL")
            except Exception as e:
                print(f"[Cloudinary] Error configuring via URL: {e}")
        
        # Fallback to individual credentials
        elif settings.CLOUDINARY_CLOUD_NAME and settings.CLOUDINARY_API_KEY and settings.CLOUDINARY_API_SECRET:
            try:
                cloudinary.config(
                    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
                    api_key=settings.CLOUDINARY_API_KEY,
                    api_secret=settings.CLOUDINARY_API_SECRET,
                    secure=True
                )
                self.configured = True
                print("[Cloudinary] Successfully configured via credentials")
            except Exception as e:
                print(f"[Cloudinary] Error configuring via credentials: {e}")
        else:
            print("[Cloudinary] Storage credentials not provided. Local file serving only.")

    def upload_image(self, file_path: str, public_id: Optional[str] = None) -> Optional[str]:
        """
        Uploads a local image file to Cloudinary.
        Returns the secure HTTPS URL or None if fails.
        """
        if not CLOUDINARY_AVAILABLE or not self.configured:
            print("[Cloudinary] Service not active. Skipping upload.")
            return None

        path = Path(file_path)
        if not path.exists():
            print(f"[Cloudinary] File does not exist: {file_path}")
            return None

        try:
            # If public ID is not specified, Cloudinary generates a random hash
            response = cloudinary.uploader.upload(
                str(path),
                public_id=public_id,
                folder="aigram_automation",
                overwrite=True,
                resource_type="image"
            )
            secure_url = response.get("secure_url")
            print(f"[Cloudinary] Uploaded image successfully: {secure_url}")
            return secure_url
        except Exception as e:
            print(f"[Cloudinary] Upload failed for {file_path}: {e}")
            return None

    def upload_carousel_post(self, run_date: str, post_rank: int, local_paths: List[str]) -> List[str]:
        """
        Uploads a list of local slide paths for a single post.
        Returns a list of public secure URLs.
        """
        if not CLOUDINARY_AVAILABLE or not self.configured:
            return []

        print(f"[Cloudinary] Uploading carousel post {post_rank} ({len(local_paths)} slides)...")
        urls = []
        for i, path in enumerate(local_paths, 1):
            public_id = f"post_{run_date}_{post_rank}_slide_{i}"
            url = self.upload_image(path, public_id=public_id)
            if url:
                urls.append(url)
            else:
                print(f"[Cloudinary] Failed to upload slide {i} for post {post_rank}")
        return urls


# Singleton service instance
cloudinary_service = CloudinaryService()
