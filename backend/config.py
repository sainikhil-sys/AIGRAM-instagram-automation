"""
config.py — Central configuration and environment loading
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"
load_dotenv(ENV_FILE)

class Settings:
    # Instagram
    INSTAGRAM_USERNAME: str = os.getenv("INSTAGRAM_USERNAME", "")
    INSTAGRAM_PASSWORD: str = os.getenv("INSTAGRAM_PASSWORD", "")

    # AI
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    NEWS_API_KEY: str = os.getenv("NEWS_API_KEY", "")

    # Schedule (hour in 24h, local time)
    RESEARCH_HOUR: int = int(os.getenv("RESEARCH_HOUR", 8))
    RESEARCH_MINUTE: int = int(os.getenv("RESEARCH_MINUTE", 0))
    PUBLISH_HOUR: int = int(os.getenv("PUBLISH_HOUR", 9))
    PUBLISH_MINUTE: int = int(os.getenv("PUBLISH_MINUTE", 0))

    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 8000))

    # Paths
    OUTPUT_DIR: Path = BASE_DIR / "output"
    IMAGES_DIR: Path = OUTPUT_DIR / "images"
    POSTS_DIR: Path = OUTPUT_DIR / "posts"
    DB_PATH: Path = BASE_DIR / "data" / "automation.db"
    FONTS_DIR: Path = Path(__file__).parent / "fonts"
    SESSION_DIR: Path = BASE_DIR / "data" / "sessions"

    def __init__(self):
        # Create required directories
        for d in [self.OUTPUT_DIR, self.IMAGES_DIR, self.POSTS_DIR,
                  self.DB_PATH.parent, self.FONTS_DIR, self.SESSION_DIR]:
            d.mkdir(parents=True, exist_ok=True)

    def update(self, **kwargs):
        """Update settings at runtime (from dashboard config)"""
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
        # Persist to .env
        env_content = ""
        env_map = {
            "INSTAGRAM_USERNAME": self.INSTAGRAM_USERNAME,
            "INSTAGRAM_PASSWORD": self.INSTAGRAM_PASSWORD,
            "GEMINI_API_KEY": self.GEMINI_API_KEY,
            "NEWS_API_KEY": self.NEWS_API_KEY,
            "RESEARCH_HOUR": self.RESEARCH_HOUR,
            "RESEARCH_MINUTE": self.RESEARCH_MINUTE,
            "PUBLISH_HOUR": self.PUBLISH_HOUR,
            "PUBLISH_MINUTE": self.PUBLISH_MINUTE,
        }
        lines = []
        for key, val in env_map.items():
            lines.append(f"{key}={val}")
        ENV_FILE.write_text("\n".join(lines))

settings = Settings()
