"""Database models for storing reminders and tracking processed mentions."""

from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from config import Config

Base = declarative_base()


class Reminder(Base):
    """A scheduled reminder to be posted at a specific time."""
    
    __tablename__ = "reminders"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # The tweet ID that triggered this reminder
    source_tweet_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # The tweet ID we need to reply to (the parent of the mention)
    reply_to_tweet_id = Column(String(50), nullable=False)
    
    # User who requested the reminder
    requester_user_id = Column(String(50), nullable=False)
    requester_username = Column(String(100), nullable=False)
    
    # Original text of the reminder request
    original_text = Column(Text, nullable=True)
    
    # Parsed duration string (e.g., "3 months")
    duration_text = Column(String(200), nullable=True)
    
    # When to send the reminder
    remind_at = Column(DateTime, nullable=False, index=True)
    
    # When the reminder was created
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Whether the reminder has been sent
    is_sent = Column(Boolean, default=False, nullable=False, index=True)
    
    # When the reminder was sent (if sent)
    sent_at = Column(DateTime, nullable=True)
    
    # The tweet ID of our reply (if sent)
    reply_tweet_id = Column(String(50), nullable=True)
    
    # Error message if sending failed
    error_message = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<Reminder {self.id}: @{self.requester_username} at {self.remind_at}>"


class ProcessedMention(Base):
    """Track mentions we've already processed to avoid duplicates."""
    
    __tablename__ = "processed_mentions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tweet_id = Column(String(50), unique=True, nullable=False, index=True)
    processed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<ProcessedMention {self.tweet_id}>"


class BotState(Base):
    """Store bot state like the last processed mention ID."""
    
    __tablename__ = "bot_state"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<BotState {self.key}={self.value}>"


# Database engine and session (lazy initialization)
_engine = None
_SessionLocal = None


def get_engine():
    """Get or create the database engine (lazy initialization)."""
    global _engine
    if _engine is None:
        _engine = create_engine(Config.DATABASE_URL, echo=False)
    return _engine


def get_session_factory():
    """Get or create the session factory."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine())
    return _SessionLocal


def init_db(max_retries=5, retry_delay=2):
    """Initialize the database tables with retry logic."""
    import time
    
    for attempt in range(max_retries):
        try:
            engine = get_engine()
            Base.metadata.create_all(engine)
            print("Database tables created successfully.")
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Database connection failed (attempt {attempt + 1}/{max_retries}): {e}")
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print(f"Failed to connect to database after {max_retries} attempts: {e}")
                return False
    return False


def get_session():
    """Get a new database session."""
    return get_session_factory()()


if __name__ == "__main__":
    init_db()

