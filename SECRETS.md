# 🔐 GitHub Secrets Configuration

This file contains all the secrets you need to add to your GitHub repository.

## 🚀 How to add Repository Secrets:

1. Go to your GitHub repo: `https://github.com/raufA1/clipflow`
2. **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add the following secrets:

## 🤖 Required Secrets

### Telegram Bot
```
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
```
**How to get**: Create a bot with @BotFather on Telegram

## 📱 Platform API Secrets (Optional)

### YouTube API
```
YOUTUBE_CLIENT_ID=your_youtube_client_id
YOUTUBE_CLIENT_SECRET=your_youtube_client_secret  
YOUTUBE_ACCESS_TOKEN=your_youtube_access_token
```
**How to get**: Google Cloud Console → Enable YouTube Data API v3

### Instagram API
```
INSTAGRAM_ACCESS_TOKEN=your_instagram_access_token
INSTAGRAM_APP_ID=your_instagram_app_id
INSTAGRAM_APP_SECRET=your_instagram_app_secret
```
**How to get**: Facebook Developers → Instagram Basic Display API

### TikTok API  
```
TIKTOK_CLIENT_KEY=your_tiktok_client_key
TIKTOK_CLIENT_SECRET=your_tiktok_client_secret
TIKTOK_ACCESS_TOKEN=your_tiktok_access_token
```
**How to get**: TikTok for Developers → TikTok API for Business

## 🚀 Deployment Secrets (For Production)

### Server Access
```
DEPLOY_HOST=your.server.ip.address
DEPLOY_USER=clipflow
DEPLOY_SSH_KEY=-----BEGIN OPENSSH PRIVATE KEY-----
your_private_ssh_key_content_here
-----END OPENSSH PRIVATE KEY-----
DEPLOY_PORT=22
```

### Database (if using PostgreSQL)
```
DB_PASSWORD=your_secure_database_password
```

### Monitoring & Notifications
```
SLACK_WEBHOOK=https://hooks.slack.com/your/webhook/url
```

## ⚙️ Repository Variables (Public settings)

In GitHub: **Settings** → **Secrets and variables** → **Actions** → **Variables** tab:

### Application Settings
```
CLIPFLOW_TIMEZONE=Asia/Baku
BRAND_NAME=Your Brand Name
BRAND_PRIMARY_COLOR=#1DA1F2
BRAND_SECONDARY_COLOR=#14171A
BRAND_WATERMARK=Created with YourBrand
LOG_LEVEL=INFO
DEPLOY_METHOD=docker
```

## 🔧 Environment-specific Secrets

### Staging Environment
Environment name: `staging`
```
TELEGRAM_BOT_TOKEN=staging_bot_token
YOUTUBE_CLIENT_ID=staging_youtube_id
# ... digər staging credentials
```

### Production Environment  
Environment name: `production`
```
TELEGRAM_BOT_TOKEN=production_bot_token
YOUTUBE_CLIENT_ID=production_youtube_id  
# ... digər production credentials
```

## 💡 Using Secrets:

### In GitHub Actions:
```yaml
- name: Deploy
  env:
    TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
    YOUTUBE_CLIENT_ID: ${{ secrets.YOUTUBE_CLIENT_ID }}
```

### In Docker Compose:
```yaml
environment:
  - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
  - YOUTUBE_CLIENT_ID=${YOUTUBE_CLIENT_ID}
```

### For Local Development:
```bash
# Create .env file
cp .env.example .env
# Edit .env and add your tokens
```

## 🔒 Security Best Practices:

1. **Never commit secrets to code**
2. **Use different tokens for production and staging**
3. **Rotate SSH keys regularly**
4. **Apply minimum permission principle**
5. **Refresh API tokens regularly**

## 🧪 Testing Secrets:

Use dummy values for test environments:
```
TELEGRAM_BOT_TOKEN=test_token
YOUTUBE_CLIENT_ID=test_youtube_id
```

These values are automatically used during testing in GitHub Actions.

---

**⚠️ WARNING**: This file is NOT for storing real secrets! It's a guide only. Add real secrets to GitHub Secrets.