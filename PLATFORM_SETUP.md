# 📱 Platform Setup Guide

Easy step-by-step guide to connect your social media accounts to ClipFlow.

## 🤖 Telegram Bot (Required)

### 1. Create Telegram Bot
1. Open Telegram and search for `@BotFather`
2. Send `/newbot` command
3. Choose a name for your bot (e.g., "My ClipFlow Bot")
4. Choose a username (e.g., "my_clipflow_bot")
5. Copy the **Bot Token** you receive

### 2. Add Bot Token to ClipFlow
```bash
# Method 1: Environment variable
export TELEGRAM_BOT_TOKEN="your_bot_token_here"

# Method 2: .env file
echo "TELEGRAM_BOT_TOKEN=your_bot_token_here" >> .env

# Method 3: GitHub Secrets (for deployment)
# Go to: Settings > Secrets and variables > Actions > New repository secret
```

### 3. Test Your Bot
```bash
python clipflow_main.py
# Send /start to your bot on Telegram
```

---

## 📺 YouTube (Optional)

### 1. Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable **YouTube Data API v3**

### 2. Create OAuth2 Credentials
1. Go to **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **OAuth 2.0 Client IDs**
3. Choose **Desktop Application**
4. Download the credentials JSON file

### 3. Get Access Token
```bash
# Install Google Auth library
pip install google-auth-oauthlib

# Run the setup wizard
python setup/youtube_setup.py
```

Or use this Python script:
```python
from google_auth_oauthlib.flow import Flow

# Replace with your credentials
CLIENT_ID = "your_client_id"
CLIENT_SECRET = "your_client_secret"
REDIRECT_URI = "http://localhost:8080/callback"

# Authorization URL
flow = Flow.from_client_config({
    "web": {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uris": [REDIRECT_URI],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token"
    }
}, scopes=["https://www.googleapis.com/auth/youtube.upload"])

flow.redirect_uri = REDIRECT_URI
auth_url, _ = flow.authorization_url(prompt='consent')
print(f"Visit this URL: {auth_url}")
```

### 4. Add to ClipFlow
```bash
# Add to .env file
YOUTUBE_CLIENT_ID=your_client_id
YOUTUBE_CLIENT_SECRET=your_client_secret
YOUTUBE_ACCESS_TOKEN=your_access_token
```

---

## 📸 Instagram (Optional)

### 1. Create Facebook App
1. Go to [Facebook Developers](https://developers.facebook.com/)
2. **Create App** > **Business** type
3. Add **Instagram Basic Display** product

### 2. Configure Instagram Basic Display
1. **Instagram Basic Display** > **Basic Display**
2. Add **Instagram Test User** (your Instagram account)
3. **Generate Token** for the test user
4. Copy the **Access Token**

### 3. Get Long-Lived Token
```bash
curl -i -X GET "https://graph.instagram.com/access_token?grant_type=ig_exchange_token&client_secret=YOUR_APP_SECRET&access_token=YOUR_SHORT_TOKEN"
```

### 4. Add to ClipFlow
```bash
# Add to .env file
INSTAGRAM_ACCESS_TOKEN=your_long_lived_token
INSTAGRAM_APP_ID=your_app_id
INSTAGRAM_APP_SECRET=your_app_secret
```

---

## 🎵 TikTok (Optional)

### 1. Apply for TikTok for Developers
1. Go to [TikTok for Developers](https://developers.tiktok.com/)
2. **Apply** for developer account
3. Wait for approval (can take few days)

### 2. Create App
1. **Manage Apps** > **Create an app**
2. Choose **TikTok API** products
3. Get **Client Key** and **Client Secret**

### 3. Get Access Token
```python
import requests

# Step 1: Get authorization code
auth_url = f"https://www.tiktok.com/auth/authorize/?client_key={CLIENT_KEY}&scope=user.info.basic,video.list,video.upload&response_type=code&redirect_uri={REDIRECT_URI}"
print(f"Visit: {auth_url}")

# Step 2: Exchange code for token
code = input("Enter authorization code: ")
token_response = requests.post("https://open-api.tiktok.com/oauth/access_token/", json={
    "client_key": CLIENT_KEY,
    "client_secret": CLIENT_SECRET,
    "code": code,
    "grant_type": "authorization_code"
})
```

### 4. Add to ClipFlow
```bash
# Add to .env file
TIKTOK_CLIENT_KEY=your_client_key
TIKTOK_CLIENT_SECRET=your_client_secret
TIKTOK_ACCESS_TOKEN=your_access_token
```

---

## 🐦 Twitter (Coming Soon)

Twitter API v2 integration is in development. Will be available in next release.

---

## 💼 LinkedIn (Coming Soon)

LinkedIn API integration is in development. Will be available in next release.

---

## 🔧 Quick Setup Commands

### All-in-One .env Setup
```bash
# Copy template
cp .env.example .env

# Edit with your credentials
nano .env
```

### Validate Setup
```bash
# Test all configured platforms
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python3 -c "
from clipflow_main import ConfigManager, ClipFlowOrchestrator
import asyncio

async def test():
    config = ConfigManager.load_from_env()
    orchestrator = ClipFlowOrchestrator(config)
    health = await orchestrator.health_check()
    print('✅ Configured platforms:')
    for platform, status in health['components']['publishers']['platforms'].items():
        status_icon = '✅' if status else '❌'
        print(f'  {status_icon} {platform.title()}')

asyncio.run(test())
"
```

### Docker Setup
```bash
# Create .env file
cp .env.example .env

# Add your tokens to .env
nano .env

# Start with Docker
docker-compose up -d

# Check status
docker-compose logs clipflow
```

---

## 🚨 Troubleshooting

### Common Issues

**❌ "Invalid Bot Token"**
- Check token format (should start with numbers and contain colon)
- Make sure no extra spaces in .env file
- Bot must be created by @BotFather

**❌ "YouTube authentication failed"**
- Enable YouTube Data API v3 in Google Cloud Console
- Check OAuth2 scopes include YouTube upload
- Refresh access token if expired

**❌ "Instagram token expired"**
- Instagram tokens expire in 60 days
- Use long-lived tokens (60 days)
- Refresh tokens programmatically

**❌ "TikTok API not approved"**
- TikTok requires manual approval for developer access
- Can take 2-7 business days
- Provide detailed use case in application

### Check Configuration
```bash
# Verify environment variables
env | grep -E "(TELEGRAM|YOUTUBE|INSTAGRAM|TIKTOK)"

# Test bot connection (requires virtual environment)
source venv/bin/activate  # if not already activated
python3 -c "
import os
from telegram import Bot
import asyncio

async def test_bot():
    bot = Bot(os.getenv('TELEGRAM_BOT_TOKEN'))
    me = await bot.get_me()
    print(f'✅ Bot connected: @{me.username}')

asyncio.run(test_bot())
"
```

### Get Support
- 📧 Issues: [GitHub Issues](https://github.com/raufA1/clipflow/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/raufA1/clipflow/discussions)
- 📖 Documentation: [Wiki](https://github.com/raufA1/clipflow/wiki)

---

## 🎉 Ready to Use!

Once you have at least the Telegram bot configured, you can start using ClipFlow:

1. **Start ClipFlow**: `python clipflow_main.py`
2. **Open Telegram** and find your bot
3. **Send `/start`** to begin
4. **Send any content** (video, image, text, audio)
5. **Choose platforms** where to publish
6. **Let AI optimize** and schedule your content! 🚀