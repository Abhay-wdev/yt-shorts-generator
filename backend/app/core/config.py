import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directories
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_DIR = BACKEND_DIR.parent
DATA_DIR = PROJECT_DIR / "data"

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI YouTube Shorts Generator"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    
    # Environment & Security
    ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = os.getenv("SECRET_KEY", "bW9jay1zZWNyZXQta2V5LWZvci1sb2NhbC1kZXZlbG9wbWVudC0xMjM=")
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*",
    ]
    
    # Database
    DATABASE_URL: str = f"sqlite:///{DATA_DIR / 'db' / 'production.db'}"
    
    # YouTube OAuth Credentials
    YOUTUBE_CLIENT_ID: str = os.getenv("YOUTUBE_CLIENT_ID", "")
    YOUTUBE_CLIENT_SECRET: str = os.getenv("YOUTUBE_CLIENT_SECRET", "")
    YOUTUBE_REDIRECT_URI: str = os.getenv("YOUTUBE_REDIRECT_URI", "http://localhost:8000/api/v1/channels/oauth/callback")
    
    # Hardware & Model Configuration
    WHISPER_MODEL_SIZE: str = os.getenv("WHISPER_MODEL_SIZE", "tiny")  # tiny, base, small
    WHISPER_COMPUTE_TYPE: str = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
    FORCE_SOFTWARE_ENCODER: bool = os.getenv("FORCE_SOFTWARE_ENCODER", "false").lower() == "true"
    MAX_CONCURRENT_HEAVY_JOBS: int = 2  # Allows concurrent GPU rendering alongside Whisper analysis on Ryzen 3 5300U
    
    # Storage Paths
    DIR_DB: Path = DATA_DIR / "db"
    DIR_UPLOADS: Path = DATA_DIR / "uploads"
    DIR_PROXIES: Path = DATA_DIR / "proxies"
    DIR_AUDIO: Path = DATA_DIR / "audio"
    DIR_TRANSCRIPTS: Path = DATA_DIR / "transcripts"
    DIR_SHORTS: Path = DATA_DIR / "shorts"
    DIR_THUMBNAILS: Path = DATA_DIR / "thumbnails"
    DIR_QC: Path = DATA_DIR / "qc"
    DIR_CACHE: Path = DATA_DIR / "cache"

    def ensure_directories(self):
        for path in [
            self.DIR_DB,
            self.DIR_UPLOADS,
            self.DIR_PROXIES,
            self.DIR_AUDIO,
            self.DIR_TRANSCRIPTS,
            self.DIR_SHORTS,
            self.DIR_THUMBNAILS,
            self.DIR_QC,
            self.DIR_CACHE,
        ]:
            path.mkdir(parents=True, exist_ok=True)

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
settings.ensure_directories()
