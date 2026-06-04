"""
config.py — Central configuration and environment loading
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)

class Settings:
    # Instagram Credentials
    INSTAGRAM_USERNAME: str = os.getenv("INSTAGRAM_USERNAME", "")
    INSTAGRAM_PASSWORD: str = os.getenv("INSTAGRAM_PASSWORD", "")

    # AI Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    NEWS_API_KEY: str = os.getenv("NEWS_API_KEY", "")

    # Schedule (hour in 24h, local time)
    RESEARCH_HOUR: int = int(os.getenv("RESEARCH_HOUR", 8))
    RESEARCH_MINUTE: int = int(os.getenv("RESEARCH_MINUTE", 0))
    PUBLISH_HOUR: int = int(os.getenv("PUBLISH_HOUR", 9))
    PUBLISH_MINUTE: int = int(os.getenv("PUBLISH_MINUTE", 0))

    # Server Settings
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

    def load_db_overrides(self, db_config: dict):
        """Update configurations from SQLite store overrides at runtime"""
        for k, v in db_config.items():
            k_upper = k.upper()
            if hasattr(self, k_upper):
                default_val = getattr(self, k_upper)
                try:
                    if isinstance(default_val, int):
                        setattr(self, k_upper, int(v))
                    elif isinstance(default_val, bool):
                        setattr(self, k_upper, v.lower() == "true")
                    else:
                        setattr(self, k_upper, v)
                except Exception as e:
                    print(f"[Config] Error applying override {k}={v}: {e}")

    def update(self, db_save_func, **kwargs):
        """Update settings at runtime and save to SQLite config_store"""
        for k, v in kwargs.items():
            k_upper = k.upper()
            if hasattr(self, k_upper):
                setattr(self, k_upper, v)
                try:
                    db_save_func(k_upper, str(v))
                except Exception as e:
                    print(f"[Config] Error saving {k_upper} to DB: {e}")

        # Try to sync to local .env if writable
        if ENV_FILE.exists():
            try:
                lines = []
                env_map = {
                    "INSTAGRAM_USERNAME": self.INSTAGRAM_USERNAME,
                    "INSTAGRAM_PASSWORD": self.INSTAGRAM_PASSWORD,
                    "GEMINI_API_KEY": self.GEMINI_API_KEY,
                    "NEWS_API_KEY": self.NEWS_API_KEY,
                    "RESEARCH_HOUR": str(self.RESEARCH_HOUR),
                    "RESEARCH_MINUTE": str(self.RESEARCH_MINUTE),
                    "PUBLISH_HOUR": str(self.PUBLISH_HOUR),
                    "PUBLISH_MINUTE": str(self.PUBLISH_MINUTE),
                    "HOST": self.HOST,
                    "PORT": str(self.PORT),
                }
                for key, val in env_map.items():
                    if val is not None:
                        lines.append(f"{key}={val}")
                ENV_FILE.write_text("\n".join(lines))
            except Exception as e:
                print(f"[Config] Could not sync local .env file: {e}")

settings = Settings()
