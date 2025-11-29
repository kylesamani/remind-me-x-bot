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


# Database engine and session
engine = create_engine(Config.DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


def init_db():
    """Initialize the database tables."""
    Base.metadata.create_all(engine)
    print("Database tables created successfully.")


def get_session():
    """Get a new database session."""
    return SessionLocal()


if __name__ == "__main__":
    init_db()

