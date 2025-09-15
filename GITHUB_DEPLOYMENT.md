# 🚀 GitHub-Based ClipFlow Deployment

> **Run ClipFlow directly on GitHub Actions - No server needed!**  
> Perfect for testing, development, or lightweight usage

---

## 🎯 Quick Start (3 Minutes)

### Step 1: Fork & Configure
1. **Fork this repository** to your GitHub account
2. **Go to Settings** → **Secrets and Variables** → **Actions**
3. **Add your tokens** as repository secrets:

### Step 2: Add Your Secrets
**Required:**
- `TELEGRAM_BOT_TOKEN` (from @BotFather)

**Optional (add for each platform you want):**
- **YouTube**: `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, `YOUTUBE_ACCESS_TOKEN`
- **Instagram**: `INSTAGRAM_ACCESS_TOKEN`, `INSTAGRAM_APP_ID`, `INSTAGRAM_APP_SECRET`  
- **TikTok**: `TIKTOK_CLIENT_KEY`, `TIKTOK_CLIENT_SECRET`, `TIKTOK_ACCESS_TOKEN`

📖 **Detailed guide**: [SECRETS_SETUP.md](SECRETS_SETUP.md) - How to get all API tokens

### Step 4: Deploy
1. **Go to Actions** tab in your forked repository
2. **Select "🚀 GitHub Deploy ClipFlow"** workflow
3. **Click "Run workflow"** → Choose **"deploy"** → **Run**
4. **Wait 2-3 minutes** for deployment to complete

### Step 5: Start Using
1. **Open Telegram** and find your bot
2. **Send `/start`** to initialize ClipFlow
3. **Upload content** and start automating! 🎉

---

## 🎛️ Workflow Actions

### Available Actions

| Action | Description | Use Case |
|--------|-------------|----------|
| **deploy** | Start ClipFlow service | First time setup or updates |
| **restart** | Restart running service | Configuration changes |
| **stop** | Stop ClipFlow service | Maintenance or cost saving |
| **status** | Check service health | Troubleshooting |

### How to Run Actions

1. **Go to Actions** tab → **🚀 GitHub Deploy ClipFlow**
2. **Click "Run workflow"**
3. **Select action** from dropdown
4. **Toggle debug mode** if needed
5. **Click "Run workflow"**

---

## 📊 Monitoring & Logs

### Deployment Reports
Each deployment generates a comprehensive report showing:
- ✅ Configuration status (which tokens are configured)
- 🤖 Service status (running/stopped)
- 🏥 System health check results
- 📱 Next steps and quick links

### Viewing Logs
1. **Go to Actions** → **Latest workflow run**
2. **Scroll to bottom** → **Artifacts section**
3. **Download** `clipflow-deployment-XXXXX.zip`
4. **Extract** and view `logs/clipflow.log`

### Real-time Monitoring
```bash
# Check if your bot is responding
# Send /start to your bot in Telegram
# Look for "Welcome to ClipFlow" message
```

---

## 💰 Cost & Limitations

### GitHub Actions Limits
- **Free tier**: 2,000 minutes/month
- **ClipFlow usage**: ~10-20 minutes per deployment
- **Estimated**: 100+ deployments per month for free

### Service Limitations
- **Runtime**: GitHub Actions runners have 6-hour timeout
- **Storage**: Temporary (lost when workflow ends)
- **Best for**: Testing, development, lightweight usage

### Cost Optimization Tips
1. **Use "stop" action** when not needed
2. **Deploy only when necessary**
3. **Use local development** for heavy testing

---

## 🔧 Configuration Management

### Environment Variables
All configuration is handled through GitHub Secrets:

```yaml
# Automatically created .env file:
TELEGRAM_BOT_TOKEN=from_github_secrets
CLIPFLOW_TIMEZONE=Asia/Baku
CLIPFLOW_GITHUB_DEPLOY=true
CLIPFLOW_DEBUG=false  # or true with debug mode
```

### Adding New Platforms
1. **Get platform API credentials** (see [SETUP_GUIDE.md](SETUP_GUIDE.md))
2. **Add secrets** to repository:
   - Settings → Secrets → Actions → New repository secret
3. **Restart deployment** with new credentials

---

## 🚨 Troubleshooting

### Common Issues

**❌ "Workflow failed at Health Check"**
- Check if `TELEGRAM_BOT_TOKEN` is correctly set
- Verify bot token format: `123456789:ABCdef...`
- Ensure bot was created by @BotFather

**❌ "ClipFlow process not found"**
- Service failed to start, check deployment logs
- Look for Python/dependency errors in artifacts
- Try running with debug mode enabled

**❌ "Bot connection failed"**
- Verify telegram bot token in secrets
- Check bot permissions with @BotFather
- Test bot manually: send `/start` in Telegram

### Debug Mode
Enable debug mode for detailed logging:
1. **Run workflow** → **Toggle "Enable debug logging"**
2. **Check artifacts** for detailed logs
3. **Review `logs/clipflow.log`** for specific errors

### Manual Testing
```yaml
# Test bot connection manually:
python3 -c "
import os, asyncio
from telegram import Bot

async def test():
    bot = Bot(os.getenv('TELEGRAM_BOT_TOKEN'))
    me = await bot.get_me()
    print(f'Bot: @{me.username}')

asyncio.run(test())
"
```

---

## 🔄 Advanced Usage

### Scheduled Deployments
Create automated deployments:

```yaml
# .github/workflows/scheduled-deploy.yml
name: Scheduled ClipFlow
on:
  schedule:
    - cron: '0 9 * * 1-5'  # Weekdays at 9 AM UTC
  
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: ./.github/workflows/github-deploy.yml
        with:
          service_action: deploy
```

### Multiple Environments
1. **Create environments**: Settings → Environments
2. **Add environment-specific secrets**
3. **Deploy to specific environment**:
   ```bash
   # Use different secrets for staging vs production
   staging: test tokens
   production: real tokens
   ```

### Custom Configuration
Fork and modify `github-deploy.yml`:
- Change timezone
- Add custom monitoring
- Integrate with external services
- Add notification webhooks

---

## 🎉 Success Indicators

### ✅ Deployment Successful When:
- GitHub Actions workflow completes with green checkmark
- Deployment report shows all platforms configured
- Telegram bot responds to `/start` command
- You can upload and process content

### 📱 Test Your Deployment:
1. **Send video** to bot → Should get platform suggestions
2. **Send image** → Should offer Instagram, Twitter options  
3. **Send text** → Should create visual posts
4. **Check `/analytics`** → Should show usage metrics

---

## 📚 Next Steps

### After Successful Deployment:
1. **Read** [SETUP_GUIDE.md](SETUP_GUIDE.md) for platform setup
2. **Join** [GitHub Discussions](https://github.com/raufA1/clipflow/discussions)
3. **Star** the repository if ClipFlow helps you! ⭐
4. **Share** your content automation success stories

### For Production Use:
- Consider **dedicated server** deployment for 24/7 operation
- Use **Docker Compose** for better resource management
- Set up **monitoring** and **backup** systems
- Review **security** considerations for production

---

<div align="center">

## 🚀 Ready to Deploy?

**[🍴 Fork Repository](https://github.com/raufA1/clipflow/fork)** → **⚙️ Add Secrets** → **▶️ Run Workflow** → **📱 Use Bot**

---

**Questions?** [💬 Ask in Discussions](https://github.com/raufA1/clipflow/discussions) • **Issues?** [🐛 Report Here](https://github.com/raufA1/clipflow/issues)

*Made with ❤️ for content creators who want automation without the server hassle*

</div>