# RemindMeX Bot (@RemindMeXplz)

A Twitter/X reminder bot that sends you a notification after a specified time. Simply tag the bot in a reply with a time duration, and it will remind you when the time is up!

## How It Works

1. **Tag the bot** in a reply to any tweet with a time duration
2. **Get a confirmation** that your reminder was set
3. **Receive a notification** when the time is up

### Example Usage

```
@RemindMeXplz 3 months
@RemindMeXplz 2 weeks
@RemindMeXplz 1 year
@RemindMeXplz 24 hours
@RemindMeXplz 30 minutes
```

## Setup Guide

### 1. X Developer Account Configuration

#### Step 1: Access the Developer Portal
1. Go to [developer.twitter.com](https://developer.twitter.com)
2. Sign in with your @RemindMeXplz account
3. Navigate to the Developer Portal

#### Step 2: Create a Project and App
1. Click **"+ Add Project"** (or use an existing project)
2. Name your project (e.g., "RemindMeX Bot")
3. Select **"Making a bot"** as your use case
4. Create an App within the project (e.g., "RemindMeXplz Bot")

#### Step 3: Configure App Permissions
1. Go to your App Settings → **"User authentication settings"**
2. Click **"Set up"**
3. Configure the following:
   - **App permissions**: Select **"Read and write"** (required to post tweets)
   - **Type of App**: Select **"Web App, Automated App or Bot"**
   - **Callback URL**: `https://your-app-name.onrender.com/callback` (or any valid URL)
   - **Website URL**: `https://your-app-name.onrender.com`
4. Save the settings

#### Step 4: Generate API Keys and Tokens
1. Go to **"Keys and tokens"** tab
2. Generate and save the following:
   - **API Key** (Consumer Key)
   - **API Key Secret** (Consumer Secret)
   - **Bearer Token**
3. Under **"Authentication Tokens"**, generate:
   - **Access Token**
   - **Access Token Secret**
   
   ⚠️ **Important**: Make sure to generate tokens with **Read and Write** permissions. If you change permissions, you must regenerate the tokens!

#### Step 5: Verify Your App
Make sure your app has:
- ✅ Essential access (Free tier is sufficient)
- ✅ Read and Write permissions
- ✅ All 5 tokens/keys generated

### 2. Local Development Setup

```bash
# Clone the repository
cd remind-me-x-bot

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy the example environment file
cp .env.example .env

# Edit .env and add your X API credentials
nano .env  # or use your preferred editor

# Initialize the database
python models.py

# Run the bot locally
python app.py
```

The bot will now be running at `http://localhost:5000`

### 3. Deploy to Render

#### Option A: Using Render Blueprint (Recommended)

1. Push this code to a GitHub repository
2. Go to [Render Dashboard](https://dashboard.render.com)
3. Click **"New"** → **"Blueprint"**
4. Connect your GitHub repository
5. Render will detect `render.yaml` and create:
   - A web service for the bot
   - A PostgreSQL database
6. Add your environment variables in the Render dashboard:
   - `X_API_KEY`
   - `X_API_SECRET`
   - `X_ACCESS_TOKEN`
   - `X_ACCESS_TOKEN_SECRET`
   - `X_BEARER_TOKEN`

#### Option B: Manual Setup

1. **Create a PostgreSQL Database**:
   - Go to Render Dashboard → **"New"** → **"PostgreSQL"**
   - Choose the Free plan
   - Note the **Internal Database URL**

2. **Create a Web Service**:
   - Go to **"New"** → **"Web Service"**
   - Connect your GitHub repository
   - Configure:
     - **Name**: `remind-me-x-bot`
     - **Runtime**: Python 3
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --preload`
   - Add environment variables (see below)

3. **Environment Variables**:
   Add these in the Render dashboard:
   ```
   X_API_KEY=your_api_key
   X_API_SECRET=your_api_secret
   X_ACCESS_TOKEN=your_access_token
   X_ACCESS_TOKEN_SECRET=your_access_token_secret
   X_BEARER_TOKEN=your_bearer_token
   DATABASE_URL=<your_postgres_connection_string>
   BOT_USERNAME=RemindMeXplz
   MENTION_CHECK_INTERVAL=60
   REMINDER_CHECK_INTERVAL=60
   ```

### 4. Keeping the Bot Alive on Free Tier

Render's free tier spins down after 15 minutes of inactivity. To keep your bot running:

#### Option 1: Use Render's Cron Job (Recommended)
Create a cron job in Render to ping your health endpoint every 14 minutes:
- **Schedule**: `*/14 * * * *`
- **Command**: `curl https://your-app-name.onrender.com/health`

#### Option 2: Use an External Service
Use a free service like [UptimeRobot](https://uptimerobot.com) or [cron-job.org](https://cron-job.org):
1. Create a free account
2. Add a new monitor
3. Set it to ping `https://your-app-name.onrender.com/health` every 5-14 minutes

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Status page with bot statistics |
| `GET /health` | Health check endpoint |
| `GET /api/stats` | JSON API for bot statistics |

## Supported Time Formats

The bot understands various time formats:

| Format | Example |
|--------|---------|
| Seconds | `30 seconds`, `30s` |
| Minutes | `15 minutes`, `15m`, `15 min` |
| Hours | `2 hours`, `2h`, `2 hrs` |
| Days | `3 days`, `3d` |
| Weeks | `2 weeks`, `2w`, `2 wks` |
| Months | `3 months`, `3mo` |
| Years | `1 year`, `1y`, `1 yr` |

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   RemindMeX Bot                      │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────────┐     ┌──────────────┐              │
│  │   Flask App  │────▶│   Scheduler  │              │
│  │  (app.py)    │     │ (APScheduler)│              │
│  └──────────────┘     └──────────────┘              │
│         │                    │                       │
│         │                    ▼                       │
│         │         ┌──────────────────┐              │
│         │         │   Bot Logic      │              │
│         │         │   (bot.py)       │              │
│         │         └──────────────────┘              │
│         │                    │                       │
│         ▼                    ▼                       │
│  ┌──────────────┐     ┌──────────────┐              │
│  │  PostgreSQL  │◀───▶│   X API      │              │
│  │  (Reminders) │     │  (tweepy)    │              │
│  └──────────────┘     └──────────────┘              │
│                                                      │
└─────────────────────────────────────────────────────┘
```

## Troubleshooting

### "Could not authenticate with X API"
- Verify all 5 API credentials are correct
- Make sure you regenerated tokens after changing permissions
- Check that the tokens belong to the @RemindMeXplz account

### "403 Forbidden" when posting tweets
- Your app needs **Read and Write** permissions
- Go to Developer Portal → App Settings → Edit permissions
- **Regenerate** your Access Token and Secret after changing permissions

### Reminders not being sent
- Check the Render logs for errors
- Verify the scheduler is running (check `/health` endpoint)
- Make sure your app isn't sleeping (see "Keeping the Bot Alive")

### Rate limiting
- The bot respects X API rate limits automatically
- Default: checks mentions every 60 seconds
- Adjust `MENTION_CHECK_INTERVAL` if needed

## License

MIT License - feel free to use and modify!

## Support

If you encounter issues, check the Render logs or open an issue on GitHub.

