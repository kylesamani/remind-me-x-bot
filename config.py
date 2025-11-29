"""Configuration management for the RemindMeX bot."""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration loaded from environment variables."""
    
    # X (Twitter) API Credentials
    X_API_KEY = os.getenv("X_API_KEY")
    X_API_SECRET = os.getenv("X_API_SECRET")
    X_ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN")
    X_ACCESS_TOKEN_SECRET = os.getenv("X_ACCESS_TOKEN_SECRET")
    X_BEARER_TOKEN = os.getenv("X_BEARER_TOKEN")
    
    # Bot configuration
    BOT_USERNAME = os.getenv("BOT_USERNAME", "RemindMeXplz")
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///reminders.db")
    
    # Fix for Render's postgres:// URL (SQLAlchemy with psycopg3 requires postgresql+psycopg://)
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
    elif DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)
    
    # Polling interval (in seconds)
    MENTION_CHECK_INTERVAL = int(os.getenv("MENTION_CHECK_INTERVAL", "60"))
    REMINDER_CHECK_INTERVAL = int(os.getenv("REMINDER_CHECK_INTERVAL", "60"))
    
    # Timezone
    TIMEZONE = os.getenv("TIMEZONE", "UTC")
    
    @classmethod
    def validate(cls):
        """Validate that all required configuration is present."""
        required = [
            ("X_API_KEY", cls.X_API_KEY),
            ("X_API_SECRET", cls.X_API_SECRET),
            ("X_ACCESS_TOKEN", cls.X_ACCESS_TOKEN),
            ("X_ACCESS_TOKEN_SECRET", cls.X_ACCESS_TOKEN_SECRET),
            ("X_BEARER_TOKEN", cls.X_BEARER_TOKEN),
        ]
        
        missing = [name for name, value in required if not value]
        
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
        return True

