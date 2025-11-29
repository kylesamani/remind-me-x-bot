"""Core bot logic for interacting with the X API."""

import logging
from datetime import datetime
from typing import Optional, List

import tweepy
from sqlalchemy.exc import IntegrityError

from config import Config
from models import get_session, Reminder, ProcessedMention, BotState, init_db
from time_parser import parse_reminder_time, time_parser

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class RemindMeBot:
    """The RemindMeX bot that monitors mentions and posts reminders."""
    
    def __init__(self):
        """Initialize the bot with X API credentials."""
        Config.validate()
        
        # API v2 client for most operations
        self.client = tweepy.Client(
            bearer_token=Config.X_BEARER_TOKEN,
            consumer_key=Config.X_API_KEY,
            consumer_secret=Config.X_API_SECRET,
            access_token=Config.X_ACCESS_TOKEN,
            access_token_secret=Config.X_ACCESS_TOKEN_SECRET,
            wait_on_rate_limit=True
        )
        
        # Get our bot's user ID
        self.bot_user = self.client.get_me()
        if self.bot_user and self.bot_user.data:
            self.bot_user_id = self.bot_user.data.id
            self.bot_username = self.bot_user.data.username
            logger.info(f"Bot initialized as @{self.bot_username} (ID: {self.bot_user_id})")
        else:
            raise RuntimeError("Could not authenticate with X API")
    
    def get_last_mention_id(self) -> Optional[str]:
        """Get the ID of the last processed mention from the database."""
        session = get_session()
        try:
            state = session.query(BotState).filter_by(key="last_mention_id").first()
            return state.value if state else None
        finally:
            session.close()
    
    def set_last_mention_id(self, mention_id: str):
        """Store the ID of the last processed mention."""
        session = get_session()
        try:
            state = session.query(BotState).filter_by(key="last_mention_id").first()
            if state:
                state.value = mention_id
                state.updated_at = datetime.utcnow()
            else:
                state = BotState(key="last_mention_id", value=mention_id)
                session.add(state)
            session.commit()
        finally:
            session.close()
    
    def is_mention_processed(self, tweet_id: str) -> bool:
        """Check if a mention has already been processed."""
        session = get_session()
        try:
            exists = session.query(ProcessedMention).filter_by(tweet_id=tweet_id).first()
            return exists is not None
        finally:
            session.close()
    
    def mark_mention_processed(self, tweet_id: str):
        """Mark a mention as processed."""
        session = get_session()
        try:
            processed = ProcessedMention(tweet_id=tweet_id)
            session.add(processed)
            session.commit()
        except IntegrityError:
            session.rollback()  # Already processed
        finally:
            session.close()
    
    def fetch_mentions(self) -> List[dict]:
        """Fetch recent mentions of the bot."""
        mentions = []
        
        try:
            since_id = self.get_last_mention_id()
            
            # Fetch mentions using the v2 API
            response = self.client.get_users_mentions(
                id=self.bot_user_id,
                since_id=since_id,
                max_results=100,
                expansions=["author_id", "in_reply_to_user_id", "referenced_tweets.id"],
                tweet_fields=["created_at", "conversation_id", "in_reply_to_user_id", "text"],
                user_fields=["username"]
            )
            
            if response.data:
                # Build a map of user IDs to usernames
                users_map = {}
                if response.includes and "users" in response.includes:
                    for user in response.includes["users"]:
                        users_map[user.id] = user.username
                
                for tweet in response.data:
                    mention = {
                        "id": str(tweet.id),
                        "text": tweet.text,
                        "author_id": str(tweet.author_id),
                        "author_username": users_map.get(tweet.author_id, "unknown"),
                        "created_at": tweet.created_at,
                        "conversation_id": str(tweet.conversation_id) if tweet.conversation_id else None,
                        "in_reply_to_user_id": str(tweet.in_reply_to_user_id) if tweet.in_reply_to_user_id else None,
                    }
                    
                    # Get the tweet being replied to (if any)
                    if tweet.referenced_tweets:
                        for ref in tweet.referenced_tweets:
                            if ref.type == "replied_to":
                                mention["replied_to_tweet_id"] = str(ref.id)
                                break
                    
                    mentions.append(mention)
                
                logger.info(f"Fetched {len(mentions)} new mentions")
            else:
                logger.debug("No new mentions found")
                
        except tweepy.TweepyException as e:
            logger.error(f"Error fetching mentions: {e}")
        
        return mentions
    
    def process_mention(self, mention: dict) -> Optional[Reminder]:
        """
        Process a single mention and create a reminder if valid.
        
        Returns the created Reminder object, or None if invalid.
        """
        tweet_id = mention["id"]
        
        # Skip if already processed
        if self.is_mention_processed(tweet_id):
            logger.debug(f"Mention {tweet_id} already processed, skipping")
            return None
        
        # Parse the time from the mention
        target_time, duration_text = parse_reminder_time(mention["text"])
        
        if not target_time:
            logger.info(f"Could not parse time from mention {tweet_id}: {mention['text']}")
            self.mark_mention_processed(tweet_id)
            # Optionally reply with an error message
            self._reply_with_error(mention)
            return None
        
        # Determine what tweet to reply to
        # If the mention is a reply to another tweet, we reply to the mention itself
        # so the user gets notified
        reply_to_id = tweet_id
        
        # Create the reminder
        session = get_session()
        try:
            reminder = Reminder(
                source_tweet_id=tweet_id,
                reply_to_tweet_id=reply_to_id,
                requester_user_id=mention["author_id"],
                requester_username=mention["author_username"],
                original_text=mention["text"],
                duration_text=duration_text,
                remind_at=target_time,
                created_at=datetime.utcnow(),
                is_sent=False
            )
            session.add(reminder)
            session.commit()
            
            logger.info(
                f"Created reminder for @{mention['author_username']}: "
                f"'{duration_text}' -> {target_time.strftime('%Y-%m-%d %H:%M:%S UTC')}"
            )
            
            # Mark as processed
            self.mark_mention_processed(tweet_id)
            
            # Send confirmation reply
            self._reply_with_confirmation(mention, target_time, duration_text)
            
            # Update last mention ID
            self.set_last_mention_id(tweet_id)
            
            return reminder
            
        except IntegrityError:
            session.rollback()
            logger.warning(f"Reminder for tweet {tweet_id} already exists")
            return None
        finally:
            session.close()
    
    def _reply_with_confirmation(self, mention: dict, target_time: datetime, duration_text: str):
        """Reply to confirm the reminder was set."""
        try:
            formatted_time = target_time.strftime("%B %d, %Y at %H:%M UTC")
            duration_str = time_parser.format_duration(target_time)
            
            reply_text = (
                f"⏰ Got it, @{mention['author_username']}! "
                f"I'll remind you in {duration_str} "
                f"(around {formatted_time})."
            )
            
            self.client.create_tweet(
                text=reply_text,
                in_reply_to_tweet_id=mention["id"]
            )
            logger.info(f"Sent confirmation reply to @{mention['author_username']}")
            
        except tweepy.TweepyException as e:
            logger.error(f"Error sending confirmation reply: {e}")
    
    def _reply_with_error(self, mention: dict):
        """Reply with an error message when we can't parse the time."""
        try:
            reply_text = (
                f"Sorry @{mention['author_username']}, I couldn't understand that time. "
                f"Try something like:\n"
                f"• @{self.bot_username} 3 months\n"
                f"• @{self.bot_username} 2 weeks\n"
                f"• @{self.bot_username} 1 year"
            )
            
            self.client.create_tweet(
                text=reply_text,
                in_reply_to_tweet_id=mention["id"]
            )
            logger.info(f"Sent error reply to @{mention['author_username']}")
            
        except tweepy.TweepyException as e:
            logger.error(f"Error sending error reply: {e}")
    
    def check_mentions(self):
        """Check for new mentions and process them."""
        logger.info("Checking for new mentions...")
        mentions = self.fetch_mentions()
        
        for mention in mentions:
            self.process_mention(mention)
    
    def get_due_reminders(self) -> List[Reminder]:
        """Get all reminders that are due to be sent."""
        session = get_session()
        try:
            now = datetime.utcnow()
            reminders = session.query(Reminder).filter(
                Reminder.is_sent == False,
                Reminder.remind_at <= now
            ).all()
            return reminders
        finally:
            session.close()
    
    def send_reminder(self, reminder: Reminder) -> bool:
        """Send a reminder reply and update the database."""
        session = get_session()
        try:
            # Refresh the reminder from the database
            reminder = session.query(Reminder).get(reminder.id)
            
            if reminder.is_sent:
                logger.debug(f"Reminder {reminder.id} already sent, skipping")
                return True
            
            # Compose the reminder message
            reply_text = (
                f"⏰ Hey @{reminder.requester_username}, your reminder is here! "
                f"You asked me to remind you about this {reminder.duration_text or 'a while'} ago."
            )
            
            # Send the reply
            response = self.client.create_tweet(
                text=reply_text,
                in_reply_to_tweet_id=reminder.reply_to_tweet_id
            )
            
            # Update the reminder
            reminder.is_sent = True
            reminder.sent_at = datetime.utcnow()
            if response.data:
                reminder.reply_tweet_id = str(response.data["id"])
            
            session.commit()
            
            logger.info(
                f"Sent reminder to @{reminder.requester_username} "
                f"(reminder ID: {reminder.id})"
            )
            return True
            
        except tweepy.TweepyException as e:
            logger.error(f"Error sending reminder {reminder.id}: {e}")
            reminder.error_message = str(e)
            session.commit()
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending reminder {reminder.id}: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    def process_due_reminders(self):
        """Check for and send all due reminders."""
        logger.info("Checking for due reminders...")
        reminders = self.get_due_reminders()
        
        if reminders:
            logger.info(f"Found {len(reminders)} due reminder(s)")
            for reminder in reminders:
                self.send_reminder(reminder)
        else:
            logger.debug("No due reminders")
    
    def get_stats(self) -> dict:
        """Get bot statistics."""
        session = get_session()
        try:
            total_reminders = session.query(Reminder).count()
            pending_reminders = session.query(Reminder).filter_by(is_sent=False).count()
            sent_reminders = session.query(Reminder).filter_by(is_sent=True).count()
            
            return {
                "total_reminders": total_reminders,
                "pending_reminders": pending_reminders,
                "sent_reminders": sent_reminders,
                "bot_username": self.bot_username
            }
        finally:
            session.close()


# Singleton bot instance
_bot_instance = None


def get_bot() -> RemindMeBot:
    """Get or create the bot instance."""
    global _bot_instance
    if _bot_instance is None:
        init_db()
        _bot_instance = RemindMeBot()
    return _bot_instance


if __name__ == "__main__":
    # Test the bot
    bot = get_bot()
    print(f"Bot authenticated as @{bot.bot_username}")
    print(f"Stats: {bot.get_stats()}")

