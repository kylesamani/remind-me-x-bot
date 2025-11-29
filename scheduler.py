"""Scheduler for running periodic bot tasks."""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from config import Config

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = None


def check_mentions_job():
    """Job to check for new mentions."""
    from bot import get_bot
    try:
        bot = get_bot()
        bot.check_mentions()
    except Exception as e:
        logger.error(f"Error in check_mentions_job: {e}")


def process_reminders_job():
    """Job to process due reminders."""
    from bot import get_bot
    try:
        bot = get_bot()
        bot.process_due_reminders()
    except Exception as e:
        logger.error(f"Error in process_reminders_job: {e}")


def start_scheduler():
    """Start the background scheduler with all jobs."""
    global scheduler
    
    if scheduler is not None:
        logger.warning("Scheduler already running")
        return scheduler
    
    scheduler = BackgroundScheduler()
    
    # Add job to check mentions
    scheduler.add_job(
        check_mentions_job,
        trigger=IntervalTrigger(seconds=Config.MENTION_CHECK_INTERVAL),
        id="check_mentions",
        name="Check for new mentions",
        replace_existing=True
    )
    
    # Add job to process due reminders
    scheduler.add_job(
        process_reminders_job,
        trigger=IntervalTrigger(seconds=Config.REMINDER_CHECK_INTERVAL),
        id="process_reminders",
        name="Process due reminders",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info(
        f"Scheduler started. "
        f"Checking mentions every {Config.MENTION_CHECK_INTERVAL}s, "
        f"processing reminders every {Config.REMINDER_CHECK_INTERVAL}s"
    )
    
    return scheduler


def stop_scheduler():
    """Stop the scheduler."""
    global scheduler
    if scheduler:
        scheduler.shutdown()
        scheduler = None
        logger.info("Scheduler stopped")


def get_scheduler():
    """Get the current scheduler instance."""
    return scheduler


if __name__ == "__main__":
    import time
    
    logging.basicConfig(level=logging.INFO)
    
    print("Starting scheduler...")
    start_scheduler()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping scheduler...")
        stop_scheduler()

