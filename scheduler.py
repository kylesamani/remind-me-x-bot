"""Scheduler for running periodic bot tasks with optimized intervals."""

import logging
import random
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from config import Config

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = None

# Track job statistics
job_stats = {
    "mentions_checked": 0,
    "reminders_processed": 0,
    "last_mention_check": None,
    "last_reminder_check": None,
    "errors": 0
}


def check_mentions_job():
    """Job to check for new mentions with statistics tracking."""
    global job_stats
    try:
        from bot import get_bot
        bot = get_bot()
        bot.check_mentions()
        job_stats["mentions_checked"] += 1
        job_stats["last_mention_check"] = datetime.utcnow()
    except Exception as e:
        job_stats["errors"] += 1
        logger.error(f"Error in check_mentions_job: {e}", exc_info=True)


def process_reminders_job():
    """Job to process due reminders with statistics tracking."""
    global job_stats
    try:
        from bot import get_bot
        bot = get_bot()
        bot.process_due_reminders()
        job_stats["reminders_processed"] += 1
        job_stats["last_reminder_check"] = datetime.utcnow()
    except Exception as e:
        job_stats["errors"] += 1
        logger.error(f"Error in process_reminders_job: {e}", exc_info=True)


def get_job_stats() -> dict:
    """Get current job statistics."""
    return {
        **job_stats,
        "last_mention_check": job_stats["last_mention_check"].isoformat() if job_stats["last_mention_check"] else None,
        "last_reminder_check": job_stats["last_reminder_check"].isoformat() if job_stats["last_reminder_check"] else None,
    }


def start_scheduler():
    """Start the background scheduler with optimized jobs."""
    global scheduler
    
    if scheduler is not None:
        logger.warning("Scheduler already running")
        return scheduler
    
    scheduler = BackgroundScheduler()
    
    # Add jitter to prevent thundering herd on startup
    # Stagger the jobs so they don't all fire at the same time
    mention_jitter = random.uniform(0, 5)  # 0-5 second random delay
    reminder_jitter = random.uniform(5, 10)  # 5-10 second random delay (offset from mentions)
    
    # Add job to check mentions (optimized to 30s default)
    scheduler.add_job(
        check_mentions_job,
        trigger=IntervalTrigger(seconds=Config.MENTION_CHECK_INTERVAL),
        id="check_mentions",
        name="Check for new mentions",
        replace_existing=True,
        next_run_time=datetime.utcnow(),  # Run immediately on startup
        jitter=int(mention_jitter)
    )
    
    # Add job to process due reminders (optimized to 30s default)
    scheduler.add_job(
        process_reminders_job,
        trigger=IntervalTrigger(seconds=Config.REMINDER_CHECK_INTERVAL),
        id="process_reminders",
        name="Process due reminders",
        replace_existing=True,
        next_run_time=datetime.utcnow(),  # Run immediately on startup
        jitter=int(reminder_jitter)
    )
    
    scheduler.start()
    logger.info(
        f"Scheduler started with optimized intervals. "
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

