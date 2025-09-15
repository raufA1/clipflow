# 🚀 ClipFlow Setup Guide

> **ClipFlow** - Universal Content Automation Platform  
> Transform your content workflow with AI-powered multi-platform publishing

---

## 📋 Quick Start Checklist

- [ ] **System Requirements** - Python 3.8+, FFmpeg
- [ ] **Telegram Bot** - Create bot and get token (Required)
- [ ] **Social Platforms** - Connect desired platforms (Optional)
- [ ] **Environment Setup** - Configure .env file
- [ ] **First Run** - Test bot and start creating content

---

## 🛠️ System Requirements

### Prerequisites
```bash
# Check Python version (3.8+ required)
python3 --version

# Install FFmpeg for video processing
sudo apt-get install ffmpeg  # Ubuntu/Debian
brew install ffmpeg          # macOS

# Install Git for repository management
sudo apt-get install git     # Ubuntu/Debian
brew install git            # macOS
```

### Development Environment
```bash
# Clone ClipFlow repository
git clone https://github.com/raufA1/clipflow.git
cd clipflow

# Run development setup validator
python3 setup_dev.py

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## 🤖 Essential Setup: Telegram Bot

**Why Telegram?** ClipFlow uses Telegram as the primary interface for content management and publishing control.

### Step 1: Create Your Bot
1. Open Telegram and search for `@BotFather`
2. Send `/newbot` command
3. Choose bot name: `"Your Brand ClipFlow Bot"`
4. Choose username: `"yourbrand_clipflow_bot"`
5. **Save the Bot Token** - you'll need this!

### Step 2: Configure Bot Token
```bash
# Add to .env file
echo "TELEGRAM_BOT_TOKEN=your_bot_token_here" >> .env

# Or set as environment variable
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
```

### Step 3: Test Bot Connection
```bash
# Run ClipFlow
python3 clipflow_main.py

# In Telegram: find your bot and send /start
# You should see welcome message and setup options
```

---

## 🌐 Platform Integration (Optional)

Connect social media platforms based on your content strategy:

| Platform | Content Types | Setup Complexity | API Approval |
|----------|---------------|------------------|--------------|
| **YouTube** | Video, Shorts | Medium | Instant |
| **Instagram** | Photos, Reels, Stories | Medium | Instant |
| **TikTok** | Short Videos | Hard | 2-7 days |
| **Twitter** | Text, Photos, Videos | Medium | Coming Soon |
| **LinkedIn** | Professional Content | Medium | Coming Soon |

### YouTube Setup (Recommended)
1. **Google Cloud Console** → Create new project
2. **Enable YouTube Data API v3**
3. **Credentials** → OAuth 2.0 Client ID → Desktop Application
4. **Download credentials.json**
5. Run setup wizard: `python3 setup/youtube_setup.py`

```bash
# Add to .env
YOUTUBE_CLIENT_ID=your_client_id
YOUTUBE_CLIENT_SECRET=your_client_secret
YOUTUBE_ACCESS_TOKEN=your_access_token
```

### Instagram Setup
1. **Facebook Developers** → Create Business App
2. **Add Instagram Basic Display** product
3. **Add Instagram Test User** (your account)
4. **Generate Access Token**
5. Convert to long-lived token (60 days)

```bash
# Add to .env
INSTAGRAM_ACCESS_TOKEN=your_long_lived_token
INSTAGRAM_APP_ID=your_app_id
INSTAGRAM_APP_SECRET=your_app_secret
```

### TikTok Setup (Advanced)
1. **Apply at TikTok for Developers** (requires business justification)
2. **Wait for approval** (2-7 business days)
3. **Create app** and get API credentials
4. **Implement OAuth2 flow** for access token

---

## ⚙️ Configuration Files

### .env Template
```bash
# === ClipFlow Configuration ===

# Telegram Bot (Required)
TELEGRAM_BOT_TOKEN=your_bot_token

# YouTube API (Optional)
YOUTUBE_CLIENT_ID=your_client_id
YOUTUBE_CLIENT_SECRET=your_client_secret  
YOUTUBE_ACCESS_TOKEN=your_access_token

# Instagram API (Optional)
INSTAGRAM_ACCESS_TOKEN=your_token
INSTAGRAM_APP_ID=your_app_id
INSTAGRAM_APP_SECRET=your_secret

# TikTok API (Optional)
TIKTOK_CLIENT_KEY=your_key
TIKTOK_CLIENT_SECRET=your_secret
TIKTOK_ACCESS_TOKEN=your_token

# ClipFlow Settings
CLIPFLOW_TIMEZONE=Asia/Baku
CLIPFLOW_DATA_DIR=data
CLIPFLOW_TEMP_DIR=temp
CLIPFLOW_BRAND_NAME="Your Brand"
CLIPFLOW_BRAND_LOGO=assets/logo.png
```

### Brand Configuration
```json
// config/brand_config.json
{
  "brand_name": "Your Brand",
  "logo_path": "assets/logo.png",
  "watermark": {
    "enabled": true,
    "position": "bottom_right",
    "opacity": 0.7
  },
  "colors": {
    "primary": "#1DA1F2",
    "secondary": "#14171A",
    "accent": "#FFD700"
  },
  "fonts": {
    "primary": "Arial",
    "secondary": "Helvetica"
  }
}
```

---

## 🎯 Usage Workflow

### Basic Content Publishing
1. **Start Bot**: `python3 clipflow_main.py`
2. **Open Telegram** → Find your bot
3. **Send Content**: Video, photo, text, or audio
4. **Choose Platforms**: Select where to publish
5. **Review & Schedule**: AI optimizes for each platform
6. **Publish**: Automatic posting with analytics

### Advanced Features
- **AI Scheduling**: Optimal posting times per platform
- **Content Optimization**: Auto-resize, crop, format for each platform
- **Brand Integration**: Logo watermarks and consistent styling
- **Analytics Dashboard**: Track performance across platforms
- **Batch Processing**: Upload multiple files at once

---

## 🔧 Validation & Testing

### System Health Check
```bash
# Run comprehensive validation
python3 setup_dev.py

# Test specific components
python3 -c "
from clipflow_main import ConfigManager, ClipFlowOrchestrator
import asyncio

async def test():
    config = ConfigManager.load_from_env()
    orchestrator = ClipFlowOrchestrator(config)
    health = await orchestrator.health_check()
    
    print('🏥 System Health Check:')
    print(f'Overall Status: {health[\"overall_status\"]}')
    
    print('\n📊 Platform Status:')
    for platform, status in health['components']['publishers']['platforms'].items():
        icon = '✅' if status else '❌'
        print(f'  {icon} {platform.title()}')

asyncio.run(test())
"
```

### Bot Connection Test
```bash
# Test Telegram bot connectivity
python3 -c "
import os, asyncio
from telegram import Bot

async def test_bot():
    if not os.getenv('TELEGRAM_BOT_TOKEN'):
        print('❌ TELEGRAM_BOT_TOKEN not set')
        return
    
    bot = Bot(os.getenv('TELEGRAM_BOT_TOKEN'))
    try:
        me = await bot.get_me()
        print(f'✅ Bot connected: @{me.username}')
        print(f'📝 Bot name: {me.first_name}')
    except Exception as e:
        print(f'❌ Bot connection failed: {e}')

asyncio.run(test_bot())
"
```

---

## 🐳 Docker Deployment

### Quick Start with Docker
```bash
# Create .env file with your tokens
cp .env.example .env
nano .env

# Build and run with Docker Compose
docker-compose up -d

# Check logs
docker-compose logs -f clipflow

# Stop service
docker-compose down
```

### Docker Configuration
```yaml
# docker-compose.yml
version: '3.8'

services:
  clipflow:
    build: .
    container_name: clipflow
    restart: unless-stopped
    env_file:
      - .env
    volumes:
      - ./data:/app/data
      - ./temp:/app/temp
      - ./config:/app/config
    ports:
      - "8000:8000"  # Health check endpoint
    healthcheck:
      test: ["CMD", "python3", "-c", "import requests; requests.get('http://localhost:8000/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
```

---

## 📊 Monitoring & Analytics

### Built-in Analytics
- **Content Performance**: Views, likes, shares per platform
- **Optimal Timing**: AI learns best posting times
- **Platform Comparison**: Cross-platform engagement analysis
- **User Behavior**: Content type preferences

### Health Monitoring
```bash
# Check service health
curl http://localhost:8000/health

# View metrics dashboard
curl http://localhost:8000/metrics
```

---

## 🚨 Troubleshooting

### Common Issues

**❌ "Invalid Bot Token"**
- Verify token format: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`
- Check for extra spaces in .env file
- Ensure bot was created by @BotFather

**❌ "FFmpeg not found"**
```bash
# Install FFmpeg
sudo apt-get update && sudo apt-get install ffmpeg
# Or on macOS: brew install ffmpeg
```

**❌ "YouTube authentication failed"**
- Enable YouTube Data API v3 in Google Cloud Console
- Check OAuth2 scopes include YouTube upload
- Refresh access token if expired

**❌ "Module not found"**
```bash
# Install in virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Debug Commands
```bash
# Check environment variables
env | grep -E "(TELEGRAM|YOUTUBE|INSTAGRAM|TIKTOK|CLIPFLOW)"

# Verbose logging
CLIPFLOW_DEBUG=true python3 clipflow_main.py

# Test individual components
python3 -m pytest tests/ -v
```

---

## 📚 Additional Resources

- **📖 API Documentation**: [GitHub Wiki](https://github.com/raufA1/clipflow/wiki)
- **💬 Community**: [GitHub Discussions](https://github.com/raufA1/clipflow/discussions) 
- **🐛 Bug Reports**: [GitHub Issues](https://github.com/raufA1/clipflow/issues)
- **🔧 Contributing**: [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 🎉 Ready to Create!

Once setup is complete:
1. **Start ClipFlow**: `python3 clipflow_main.py`
2. **Open Telegram** and find your bot
3. **Send `/start`** to initialize
4. **Upload content** (video, photo, text, audio)
5. **Select platforms** and let AI optimize
6. **Watch your content** reach audiences across platforms! 🚀

---

<div align="center">

**Made with ❤️ by the ClipFlow Team**

[⭐ Star on GitHub](https://github.com/raufA1/clipflow) • [📱 Follow Updates](https://t.me/clipflow_updates) • [💼 Enterprise](mailto:enterprise@clipflow.io)

</div>