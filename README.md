<div align="center">

![ClipFlow Logo](assets/clipflow_logo.png)

# 🚀 ClipFlow - Universal Content Automation Platform

> **AI-Powered Multi-Platform Content Publishing**  
> Transform any content (video, photo, text, audio) into optimized posts across YouTube, Instagram, TikTok, and more!

[![GitHub Stars](https://img.shields.io/github/stars/raufA1/clipflow?style=for-the-badge)](https://github.com/raufA1/clipflow/stargazers)
[![License](https://img.shields.io/github/license/raufA1/clipflow?style=for-the-badge)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python)](https://python.org)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-26A5E4?style=for-the-badge&logo=telegram)](https://t.me/clipflow_updates)

</div>

ClipFlow is a comprehensive automation platform that transforms any content (video, image, text, audio) into optimized posts for YouTube, Instagram, TikTok, Twitter, and LinkedIn. Control everything through a simple Telegram bot interface.

## ✨ Key Features

### 🤖 Universal Telegram Bot Interface
- Send any content type → Get optimized posts for all platforms
- Smart content analysis and platform recommendations  
- Real-time scheduling suggestions and performance insights
- One interface for all your social media automation

### 📹 Advanced Content Processing
- **Video**: Platform-specific optimization (9:16, 1:1, 16:9), smart cropping, brand overlays
- **Images**: Automatic resizing, style effects, carousel generation, brand watermarks
- **Text**: Beautiful visual posts, quote cards, announcement graphics, professional layouts
- **Audio**: Waveform visualizations, podcast clips, audiograms with animations

### 🎯 AI-Powered Scheduling
- Machine learning optimization based on your audience
- Thompson Sampling for exploration/exploitation balance
- Cross-platform timing coordination (avoid posting conflicts)
- Learns from your performance data to improve recommendations

### 📊 Comprehensive Analytics
- Real-time performance tracking across all platforms
- Growth metrics, engagement analysis, ROI insights
- Automated report generation with actionable recommendations
- Export capabilities (CSV, JSON) for deeper analysis

### 🚀 Multi-Platform Publishing
- **YouTube**: Shorts and regular videos with SEO optimization
- **Instagram**: Posts, Reels, Stories, and Carousels
- **TikTok**: Optimized vertical videos with trending hashtags
- **Twitter**: Images, videos, threads, and text posts
- **LinkedIn**: Professional content formatting and scheduling

## 🏗️ Architecture

```
ClipFlow/
├─ services/
│  ├─ bot/               # Telegram bot interface
│  └─ processor/         # Content processing pipeline
├─ core/
│  ├─ video_processor.py     # FFmpeg video processing
│  ├─ image_processor.py     # PIL image processing  
│  ├─ text_to_visual.py      # Text-to-image generation
│  ├─ audio_processor.py     # Audio visualization
│  ├─ publishers/            # Platform adapters
│  ├─ scheduler/             # AI scheduling system
│  └─ analytics/             # Metrics & reporting
├─ data/                     # User data & metrics
├─ temp/                     # Temporary processing files
└─ clipflow_main.py         # Main orchestrator
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- FFmpeg (for video processing)
- Telegram Bot Token ([Get from @BotFather](https://t.me/botfather))
- Platform API credentials (optional but recommended)

### 🚀 GitHub Actions Deployment (Recommended)

**No server needed! Run ClipFlow directly on GitHub:**

1. **[Fork this repository](https://github.com/raufA1/clipflow/fork)**
2. **Add secrets**: Settings → Secrets → Actions
   - `TELEGRAM_BOT_TOKEN` (required - from @BotFather)
   - YouTube, Instagram, TikTok tokens (optional)
3. **Deploy**: Actions → "🚀 GitHub Deploy ClipFlow" → Run workflow
4. **Start using**: Open Telegram → Send `/start` to your bot

📖 **Guides**: [GitHub Deploy](GITHUB_DEPLOYMENT.md) • [All API Tokens](SECRETS_SETUP.md)

### 🐳 Docker Installation

1. **Clone and start with Docker**
```bash
git clone https://github.com/raufA1/clipflow.git
cd clipflow

# Copy environment template
cp .env.example .env

# Edit .env with your tokens
nano .env

# Start with Docker Compose
docker-compose up -d

# Check logs
docker-compose logs -f clipflow
```

### 💻 Manual Installation

1. **Clone the repository**
```bash
git clone https://github.com/raufA1/clipflow.git
cd clipflow
```

2. **Install dependencies**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

3. **Install FFmpeg**
```bash
# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

4. **Configure environment**
```bash
# Copy example config
cp .env.example .env

# Edit with your credentials
nano .env
```

5. **Run ClipFlow**
```bash
python clipflow_main.py
```

### 🔑 Platform Setup

- **Full Setup**: [SETUP_GUIDE.md](SETUP_GUIDE.md) - Complete configuration guide
- **GitHub Deploy**: [GITHUB_DEPLOYMENT.md](GITHUB_DEPLOYMENT.md) - Run on GitHub Actions (no server needed!)

## ⚙️ Configuration

### Environment Variables
```env
# Required
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Optional Platform Credentials
YOUTUBE_CLIENT_ID=your_youtube_client_id
YOUTUBE_CLIENT_SECRET=your_youtube_client_secret
YOUTUBE_ACCESS_TOKEN=your_youtube_access_token

INSTAGRAM_ACCESS_TOKEN=your_instagram_access_token
INSTAGRAM_APP_ID=your_instagram_app_id
INSTAGRAM_APP_SECRET=your_instagram_app_secret

TIKTOK_CLIENT_KEY=your_tiktok_client_key
TIKTOK_CLIENT_SECRET=your_tiktok_client_secret
TIKTOK_ACCESS_TOKEN=your_tiktok_access_token

# Settings
CLIPFLOW_TIMEZONE=Asia/Baku
CLIPFLOW_USE_ENV=true
```

### JSON Configuration
Alternatively, edit `config.json`:
```json
{
  "telegram_bot_token": "your_bot_token",
  "timezone": "Asia/Baku",
  "platform_credentials": {
    "youtube": {
      "client_id": "...",
      "client_secret": "...",
      "access_token": "..."
    }
  },
  "default_brand_config": {
    "name": "Your Brand",
    "primary_color": "#1DA1F2",
    "logo_path": "path/to/logo.png"
  }
}
```

## 🤖 Bot Commands

### Basic Commands
- `/start` - Welcome and setup wizard
- `/profile` - Configure language, timezone, brand settings
- `/platforms` - Connect social media accounts
- `/schedule` - View and manage scheduled posts
- `/analytics` - Get performance insights
- `/help` - Show all available commands

### Content Workflow
1. **Send content** → Bot analyzes and suggests platforms
2. **Select platforms** → Content gets processed for each platform
3. **Choose timing** → AI suggests optimal posting times
4. **Confirm** → Content gets published or scheduled
5. **Track results** → Automatic metrics collection and learning

## 📊 Usage Examples

### Video Content
```
User: *sends video*
Bot: 📹 Video Analysis:
     Duration: 45s, Aspect: 0.56 (vertical)
     Suggested platforms: TikTok, Instagram Reels, YouTube Shorts
     
     [🎵 TikTok] [📸 Instagram] [📺 YouTube] [🎯 All Platforms]
```

### Text Content  
```
User: "Just launched our new product! 🚀"
Bot: 📝 Text Analysis:
     Length: 34 chars
     Suggested formats: Twitter Post, IG Story, Quote Visual
     
     [🐦 Twitter] [📱 IG Story] [🎨 Visual] [💼 LinkedIn]
```

### Scheduling
```
Bot: ⏰ Optimal posting times:
     • Instagram: Wednesday 19:00 (Score: 0.85)
     • TikTok: Thursday 21:00 (Score: 0.78)  
     • YouTube: Sunday 20:00 (Score: 0.72)
     
     [📅 Schedule All] [⚡ Publish Now] [⚙️ Custom Times]
```

## 🎨 Customization

### Brand Configuration
```python
brand_config = {
    "name": "Your Brand",
    "logo_path": "assets/logo.png",
    "primary_color": "#1DA1F2",
    "secondary_color": "#14171A", 
    "accent_color": "#FFD700",
    "watermark_text": "@yourbrand",
    "fonts": {
        "primary": "Arial",
        "secondary": "Helvetica"
    }
}
```

### Content Templates
Create custom templates for different content types:
- Quote cards with your brand colors
- Professional LinkedIn posts
- Trending TikTok formats
- Instagram story templates

## 📈 Analytics & Reporting

### Real-time Metrics
- Views, likes, comments, shares across all platforms
- Engagement rates and click-through rates
- Audience growth and retention metrics
- Cross-platform performance comparisons

### AI Insights
- Best posting times for each platform
- Content type performance analysis
- Hashtag effectiveness tracking
- Audience behavior patterns

### Export Options
- CSV exports for spreadsheet analysis
- JSON exports for custom integrations
- PDF reports for presentations
- Automated weekly/monthly reports

## 🔧 Development

### Running Tests
```bash
pytest tests/
```

### Code Formatting
```bash
black clipflow/
flake8 clipflow/
```

### Adding New Platforms
1. Create publisher in `core/publishers/`
2. Implement `BasePublisher` interface
3. Add authentication flow
4. Register in `PublishManager`

### Custom Content Processors
1. Extend `ContentProcessor` class
2. Add new content type enum
3. Implement processing logic
4. Register in content pipeline

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/raufA1/clipflow/issues)
- **Discussions**: [GitHub Discussions](https://github.com/raufA1/clipflow/discussions)
- **Documentation**: [Wiki](https://github.com/raufA1/clipflow/wiki)

## 🚀 Roadmap

### Phase 1 (Current)
- ✅ Core content processing
- ✅ Multi-platform publishing  
- ✅ AI scheduling
- ✅ Analytics system
- ✅ Telegram bot interface

### Phase 2 (Next)
- 🔄 Advanced AI features (GPT integration)
- 🔄 Web dashboard interface
- 🔄 Team collaboration features
- 🔄 Advanced analytics (competitor analysis)
- 🔄 Mobile app

### Phase 3 (Future)
- 📋 Live streaming automation
- 📋 Community management tools
- 📋 Monetization tracking
- 📋 White-label solutions
- 📋 Enterprise features

---

<div align="center">

---

**Made with ❤️ by the ClipFlow Team**

[⭐ Star on GitHub](https://github.com/raufA1/clipflow) • [📚 Documentation](SETUP_GUIDE.md) • [💬 Community](https://github.com/raufA1/clipflow/discussions) • [🐛 Report Issues](https://github.com/raufA1/clipflow/issues)

*ClipFlow - Because your content deserves to be everywhere* 🌍

</div>