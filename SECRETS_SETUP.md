# 🔐 GitHub Secrets Setup Guide

> **Complete guide to configure all platform credentials as GitHub Secrets**

---

## 🚀 Quick Setup Overview

1. **Go to your forked repository**
2. **Settings** → **Secrets and Variables** → **Actions**
3. **Click "New repository secret"** for each platform
4. **Add secrets** from the tables below
5. **Deploy** and start using ClipFlow!

---

## 🤖 Telegram Bot (Required)

### Get Token from @BotFather

1. Open Telegram → Search `@BotFather`
2. Send `/newbot`
3. Choose bot name: `"YourBrand ClipFlow Bot"`
4. Choose username: `"yourbrand_clipflow_bot"`
5. **Copy the token** (looks like: `123456789:ABCdef...`)

### Add to GitHub Secrets

| Secret Name | Description | Example Value |
|------------|-------------|---------------|
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather | `123456789:ABCdefGHIjklMNOpqrsTUVwxyz` |

---

## 📺 YouTube API (Optional)

### Setup Process
1. **[Google Cloud Console](https://console.cloud.google.com/)** → Create project
2. **Enable** "YouTube Data API v3"
3. **Credentials** → "OAuth 2.0 Client IDs" → "Desktop Application"
4. **Download** credentials.json
5. Run authorization flow (see [SETUP_GUIDE.md](SETUP_GUIDE.md))

### GitHub Secrets

| Secret Name | Description | Example Value |
|------------|-------------|---------------|
| `YOUTUBE_CLIENT_ID` | OAuth2 Client ID | `123456789-abcdef.apps.googleusercontent.com` |
| `YOUTUBE_CLIENT_SECRET` | OAuth2 Client Secret | `GOCSPX-abcdef123456789` |
| `YOUTUBE_ACCESS_TOKEN` | Access Token | `ya29.a0AbCdEf123456789...` |
| `YOUTUBE_REFRESH_TOKEN` | Refresh Token (optional) | `1//0AbCdEf123456789...` |

---

## 📸 Instagram API (Optional)

### Setup Process
1. **[Facebook Developers](https://developers.facebook.com/)** → Create App
2. **Add** "Instagram Basic Display" product
3. **Add Instagram Test User** (your account)
4. **Generate Access Token**
5. **Convert to long-lived token** (60 days)

### GitHub Secrets

| Secret Name | Description | Example Value |
|------------|-------------|---------------|
| `INSTAGRAM_ACCESS_TOKEN` | Long-lived access token | `IGQVJXabc123def456...` |
| `INSTAGRAM_APP_ID` | Facebook App ID | `123456789012345` |
| `INSTAGRAM_APP_SECRET` | Facebook App Secret | `abcdef123456789abcdef123456789ab` |

---

## 🎵 TikTok API (Optional)

### Setup Process
1. **[TikTok for Developers](https://developers.tiktok.com/)** → Apply for access
2. **Wait for approval** (2-7 business days)
3. **Create App** → Get credentials
4. **Implement OAuth2 flow**

### GitHub Secrets

| Secret Name | Description | Example Value |
|------------|-------------|---------------|
| `TIKTOK_CLIENT_KEY` | TikTok App Client Key | `aw123abc456def789ghi` |
| `TIKTOK_CLIENT_SECRET` | TikTok App Client Secret | `abc123def456ghi789jkl012mno345pqr678` |
| `TIKTOK_ACCESS_TOKEN` | TikTok Access Token | `act.generic.123abc456def789ghi012jkl345...` |

---

## 🐦 Twitter API (Coming Soon)

### Setup Process
1. **[Twitter Developer Portal](https://developer.twitter.com/)** → Create App
2. **Generate** API Keys and Access Tokens
3. **Enable** Twitter API v2

### GitHub Secrets (When Available)

| Secret Name | Description | Example Value |
|------------|-------------|---------------|
| `TWITTER_API_KEY` | Twitter API Key | `abc123def456ghi789jkl012mno345` |
| `TWITTER_API_SECRET` | Twitter API Secret Key | `abc123def456ghi789jkl012mno345pqr678stu901vwx234` |
| `TWITTER_ACCESS_TOKEN` | Access Token | `123456789-abc123def456ghi789jkl012mno345pqr678` |
| `TWITTER_ACCESS_SECRET` | Access Token Secret | `abc123def456ghi789jkl012mno345pqr678stu901vwx` |

---

## 💼 LinkedIn API (Coming Soon)

### Setup Process
1. **[LinkedIn Developers](https://www.linkedin.com/developers/)** → Create App
2. **Request** publishing permissions
3. **Generate** access tokens

### GitHub Secrets (When Available)

| Secret Name | Description | Example Value |
|------------|-------------|---------------|
| `LINKEDIN_CLIENT_ID` | LinkedIn Client ID | `123456789abcdef` |
| `LINKEDIN_CLIENT_SECRET` | LinkedIn Client Secret | `abcdef123456789` |
| `LINKEDIN_ACCESS_TOKEN` | LinkedIn Access Token | `AQVabc123def456ghi789jkl012...` |

---

## ⚙️ ClipFlow Settings (Optional)

### Advanced Configuration

| Secret Name | Description | Default Value | Options |
|------------|-------------|---------------|---------|
| `CLIPFLOW_TIMEZONE` | Your timezone | `Asia/Baku` | Any valid timezone |
| `CLIPFLOW_DEBUG` | Enable debug logging | `false` | `true` / `false` |
| `CLIPFLOW_DATA_DIR` | Data directory | `data` | Any valid path |
| `CLIPFLOW_TEMP_DIR` | Temp directory | `temp` | Any valid path |
| `CLIPFLOW_BRAND_NAME` | Your brand name | `ClipFlow` | Any string |

---

## 🔧 Adding Secrets Step-by-Step

### 1. Navigate to Secrets
```
Your Repository → Settings → Secrets and Variables → Actions
```

### 2. Add New Secret
```
Click "New repository secret"
Name: TELEGRAM_BOT_TOKEN
Secret: paste_your_bot_token_here
Click "Add secret"
```

### 3. Repeat for All Platforms
Add secrets for each platform you want to use:
- ✅ Telegram (required)
- ⚡ YouTube (recommended)
- 📸 Instagram (popular)
- 🎵 TikTok (if approved)

### 4. Verify Configuration
After adding secrets, run deployment:
```
Actions → "🚀 GitHub Deploy ClipFlow" → Run workflow → deploy
```

---

## 🔍 Verification & Testing

### Check Secret Configuration
The deployment workflow automatically shows which platforms are configured:

```
📋 Configuration Status
- ✅ Telegram Bot
- ✅ YouTube API  
- ❌ Instagram API
- ❌ TikTok API
```

### Test Individual Platforms

#### Telegram Bot
```bash
# In your bot chat:
/start
# Should respond with welcome message
```

#### YouTube
```bash
# Send video to bot:
# Should show YouTube as option
📺 [YouTube Shorts] button
```

#### Instagram
```bash
# Send photo to bot:
# Should show Instagram options
📸 [Instagram Post] [Instagram Story] buttons
```

---

## 🚨 Security Best Practices

### ✅ Do's
- **Keep tokens private** - never share in public
- **Use repository secrets** - not environment variables in code
- **Regenerate tokens** periodically
- **Remove unused** platform access
- **Monitor API usage** to prevent quota exceeded

### ❌ Don'ts  
- **Never commit** tokens to git repository
- **Don't share** screenshots of tokens
- **Don't use** production tokens for testing
- **Don't store** tokens in plain text files

### 🔒 Token Security
- **Telegram tokens** don't expire but can be regenerated
- **YouTube tokens** may expire (use refresh tokens)
- **Instagram tokens** expire in 60 days (use long-lived)
- **TikTok tokens** have various expiration periods

---

## 🆘 Troubleshooting

### Common Issues

**❌ "Secret not found" Error**
- Check secret name matches exactly (case-sensitive)
- Verify secret is added to correct repository
- Ensure no extra spaces in secret value

**❌ "Invalid token format" Error**
- Telegram: Should start with numbers, contain colon
- YouTube: Should be long base64-like string
- Instagram: Should start with `IGQV` or similar

**❌ "Insufficient permissions" Error**
- YouTube: Ensure "upload" scope is enabled
- Instagram: Check test user permissions
- TikTok: Verify app approval and scopes

### Debug Mode
Enable debug logging in deployment:
```
Actions → Run workflow → Toggle "Enable debug logging" → Run
```

### Manual Testing
Test individual secrets:
```python
# Test Telegram bot
import os
from telegram import Bot
bot = Bot(os.getenv('TELEGRAM_BOT_TOKEN'))
print(bot.get_me())
```

---

## 📊 Platform Priority Recommendations

### For Beginners
1. **Telegram Bot** ⭐⭐⭐ (Required)
2. **YouTube** ⭐⭐⭐ (Easy setup, big reach)
3. **Instagram** ⭐⭐ (Popular, good engagement)

### For Advanced Users
1. **All above** ⭐⭐⭐
2. **TikTok** ⭐⭐ (High engagement, approval needed)
3. **Twitter** ⭐ (Coming soon)
4. **LinkedIn** ⭐ (Professional content)

### Cost Considerations
- **Telegram**: Free
- **YouTube**: Free (with quotas)
- **Instagram**: Free (with rate limits)
- **TikTok**: Free (approval required)

---

## 🎉 Ready to Deploy?

Once you've added your secrets:

1. **Go to Actions** tab
2. **Run "🚀 GitHub Deploy ClipFlow"** workflow  
3. **Choose "deploy"** action
4. **Wait for completion** (2-3 minutes)
5. **Open Telegram** → Send `/start` to your bot
6. **Start automating** your content! 🚀

---

<div align="center">

**Need Help?** 

[💬 Ask in Discussions](https://github.com/raufA1/clipflow/discussions) • [🐛 Report Issues](https://github.com/raufA1/clipflow/issues) • [📖 Full Setup Guide](SETUP_GUIDE.md)

---

*Secure your tokens, automate your content* 🔐✨

</div>