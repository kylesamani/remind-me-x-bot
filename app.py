"""Flask web application for the RemindMeX bot."""

import logging
import os
from datetime import datetime

from flask import Flask, jsonify, render_template_string

from config import Config
from models import init_db, get_session, Reminder
from scheduler import start_scheduler, stop_scheduler

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# HTML template for the status page
STATUS_PAGE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RemindMeX Bot Status</title>
    <link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Sora:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-primary: #0a0a0f;
            --bg-secondary: #12121a;
            --bg-card: #1a1a24;
            --accent-cyan: #00f5d4;
            --accent-magenta: #f72585;
            --accent-yellow: #fee440;
            --text-primary: #ffffff;
            --text-secondary: #a0a0b0;
            --border-color: #2a2a3a;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Sora', sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            position: relative;
            overflow-x: hidden;
        }
        
        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: 
                radial-gradient(ellipse at 20% 20%, rgba(0, 245, 212, 0.08) 0%, transparent 50%),
                radial-gradient(ellipse at 80% 80%, rgba(247, 37, 133, 0.08) 0%, transparent 50%),
                radial-gradient(ellipse at 50% 50%, rgba(254, 228, 64, 0.03) 0%, transparent 70%);
            pointer-events: none;
            z-index: 0;
        }
        
        .container {
            max-width: 900px;
            margin: 0 auto;
            padding: 60px 24px;
            position: relative;
            z-index: 1;
        }
        
        header {
            text-align: center;
            margin-bottom: 60px;
        }
        
        .logo {
            font-family: 'Space Mono', monospace;
            font-size: 3rem;
            font-weight: 700;
            background: linear-gradient(135deg, var(--accent-cyan) 0%, var(--accent-magenta) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 12px;
            letter-spacing: -2px;
        }
        
        .tagline {
            color: var(--text-secondary);
            font-size: 1.1rem;
            font-weight: 300;
        }
        
        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 10px 20px;
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 50px;
            margin-top: 24px;
            font-family: 'Space Mono', monospace;
            font-size: 0.9rem;
        }
        
        .status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: var(--accent-cyan);
            box-shadow: 0 0 12px var(--accent-cyan);
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 20px;
            margin-bottom: 48px;
        }
        
        .stat-card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 28px;
            transition: all 0.3s ease;
        }
        
        .stat-card:hover {
            border-color: var(--accent-cyan);
            transform: translateY(-2px);
        }
        
        .stat-label {
            font-size: 0.85rem;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
        }
        
        .stat-value {
            font-family: 'Space Mono', monospace;
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--accent-cyan);
        }
        
        .stat-card:nth-child(2) .stat-value { color: var(--accent-yellow); }
        .stat-card:nth-child(3) .stat-value { color: var(--accent-magenta); }
        
        .section {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 32px;
            margin-bottom: 24px;
        }
        
        .section-title {
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .section-title::before {
            content: '';
            width: 4px;
            height: 20px;
            background: var(--accent-cyan);
            border-radius: 2px;
        }
        
        .reminder-list {
            list-style: none;
        }
        
        .reminder-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 16px 0;
            border-bottom: 1px solid var(--border-color);
        }
        
        .reminder-item:last-child {
            border-bottom: none;
        }
        
        .reminder-user {
            font-family: 'Space Mono', monospace;
            color: var(--accent-cyan);
        }
        
        .reminder-time {
            color: var(--text-secondary);
            font-size: 0.9rem;
        }
        
        .empty-state {
            text-align: center;
            padding: 40px;
            color: var(--text-secondary);
        }
        
        .usage-code {
            background: var(--bg-secondary);
            border-radius: 8px;
            padding: 20px;
            font-family: 'Space Mono', monospace;
            font-size: 0.9rem;
            color: var(--accent-yellow);
            overflow-x: auto;
        }
        
        footer {
            text-align: center;
            padding: 40px 0;
            color: var(--text-secondary);
            font-size: 0.85rem;
        }
        
        footer a {
            color: var(--accent-cyan);
            text-decoration: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="logo">@RemindMeXplz</div>
            <p class="tagline">Your friendly X reminder bot</p>
            <div class="status-badge">
                <span class="status-dot"></span>
                <span>Bot Online</span>
            </div>
        </header>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Total Reminders</div>
                <div class="stat-value">{{ stats.total_reminders }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Pending</div>
                <div class="stat-value">{{ stats.pending_reminders }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Delivered</div>
                <div class="stat-value">{{ stats.sent_reminders }}</div>
            </div>
        </div>
        
        <div class="section">
            <h2 class="section-title">How to Use</h2>
            <div class="usage-code">
                @RemindMeXplz 3 months<br>
                @RemindMeXplz 2 weeks<br>
                @RemindMeXplz 1 year<br>
                @RemindMeXplz 24 hours
            </div>
        </div>
        
        <div class="section">
            <h2 class="section-title">Upcoming Reminders</h2>
            {% if upcoming_reminders %}
            <ul class="reminder-list">
                {% for reminder in upcoming_reminders %}
                <li class="reminder-item">
                    <span class="reminder-user">@{{ reminder.requester_username }}</span>
                    <span class="reminder-time">{{ reminder.remind_at.strftime('%b %d, %Y %H:%M UTC') }}</span>
                </li>
                {% endfor %}
            </ul>
            {% else %}
            <div class="empty-state">
                No upcoming reminders yet. Tag @RemindMeXplz to set one!
            </div>
            {% endif %}
        </div>
        
        <footer>
            <p>Server Time: {{ current_time }}</p>
            <p style="margin-top: 8px;">Built with ❤️ for the X community</p>
        </footer>
    </div>
</body>
</html>
"""


@app.route("/")
def index():
    """Render the status page."""
    try:
        from bot import get_bot
        bot = get_bot()
        stats = bot.get_stats()
    except Exception as e:
        logger.error(f"Error getting bot stats: {e}")
        stats = {
            "total_reminders": 0,
            "pending_reminders": 0,
            "sent_reminders": 0,
            "bot_username": Config.BOT_USERNAME
        }
    
    # Get upcoming reminders
    session = get_session()
    try:
        upcoming_reminders = session.query(Reminder).filter(
            Reminder.is_sent == False
        ).order_by(Reminder.remind_at).limit(10).all()
    finally:
        session.close()
    
    return render_template_string(
        STATUS_PAGE_HTML,
        stats=stats,
        upcoming_reminders=upcoming_reminders,
        current_time=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    )


@app.route("/health")
def health():
    """Health check endpoint for Render."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    })


@app.route("/api/stats")
def api_stats():
    """API endpoint for bot statistics."""
    try:
        from bot import get_bot
        bot = get_bot()
        stats = bot.get_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({"error": str(e)}), 500


def create_app():
    """Create and configure the Flask application."""
    # Initialize database
    init_db()
    
    # Start the scheduler when the app starts
    start_scheduler()
    
    # Run initial checks
    try:
        from bot import get_bot
        bot = get_bot()
        logger.info(f"Bot initialized as @{bot.bot_username}")
    except Exception as e:
        logger.error(f"Error initializing bot: {e}")
    
    return app


# For running directly
if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

