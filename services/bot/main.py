#!/usr/bin/env python3
"""
ClipFlow Universal Content Automation Bot
Handles: Video, Photo, Text, Audio content → Multi-platform publishing
"""

import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import json
from pathlib import Path

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class ClipFlowBot:
    def __init__(self, token: str):
        self.token = token
        self.app = Application.builder().token(token).build()
        self.user_data_dir = Path("data/users")
        self.user_data_dir.mkdir(parents=True, exist_ok=True)
        
        # Register handlers
        self._register_handlers()
    
    def _register_handlers(self):
        """Register all bot handlers"""
        # Commands
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("profile", self.profile_command))
        self.app.add_handler(CommandHandler("platforms", self.platforms_command))
        self.app.add_handler(CommandHandler("templates", self.templates_command))
        self.app.add_handler(CommandHandler("schedule", self.schedule_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        
        # Content handlers
        self.app.add_handler(MessageHandler(filters.VIDEO, self.handle_video))
        self.app.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
        self.app.add_handler(MessageHandler(filters.AUDIO | filters.VOICE, self.handle_audio))
        self.app.add_handler(MessageHandler(filters.Document.ALL, self.handle_document))
        
        # Callback handlers
        self.app.add_handler(CallbackQueryHandler(self.handle_callback))
    
    def get_user_data(self, user_id: int) -> dict:
        """Load user configuration"""
        user_file = self.user_data_dir / f"{user_id}.json"
        if user_file.exists():
            return json.loads(user_file.read_text())
        return self._default_user_config()
    
    def save_user_data(self, user_id: int, data: dict):
        """Save user configuration"""
        user_file = self.user_data_dir / f"{user_id}.json"
        user_file.write_text(json.dumps(data, indent=2))
    
    def _default_user_config(self) -> dict:
        return {
            "language": "en",
            "timezone": "Asia/Baku",
            "brand": {
                "name": "",
                "logo_url": "",
                "colors": {"primary": "#1DA1F2", "secondary": "#14171A"},
                "fonts": {"primary": "Arial", "secondary": "Helvetica"}
            },
            "platforms": {
                "youtube": {"enabled": False, "channel_id": ""},
                "tiktok": {"enabled": False, "username": ""},
                "instagram": {"enabled": False, "username": ""},
                "twitter": {"enabled": False, "username": ""},
                "linkedin": {"enabled": False, "profile_id": ""}
            },
            "preferences": {
                "auto_schedule": True,
                "cross_promote": True,
                "default_privacy": "public"
            },
            "templates": {}
        }
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Welcome message and setup"""
        user = update.effective_user
        user_data = self.get_user_data(user.id)
        
        welcome_text = f"""
🎬 Welcome to ClipFlow, {user.first_name}!

Universal Content Automation Platform
📹 Video → Shorts/Reels/TikTok
📸 Photos → Stories/Posts/Carousels  
📝 Text → Threads/Articles/Stories
🎵 Audio → Audiograms/Podcasts

Setup:
/profile - Configure language & brand
/platforms - Connect social accounts
/templates - Create content templates

Just send me any content and I'll help you publish everywhere! 🚀
        """
        
        keyboard = [
            [InlineKeyboardButton("🔧 Setup Profile", callback_data="setup_profile")],
            [InlineKeyboardButton("🔗 Connect Platforms", callback_data="setup_platforms")],
            [InlineKeyboardButton("📚 View Templates", callback_data="view_templates")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    
    async def handle_video(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle video content"""
        user_id = update.effective_user.id
        user_data = self.get_user_data(user_id)
        
        video = update.message.video
        caption = update.message.caption or ""
        
        # Detect video characteristics
        duration = video.duration
        aspect_ratio = video.width / video.height if video.height else 1
        
        # Suggest platforms based on video properties
        suggested_platforms = self._suggest_platforms_for_video(duration, aspect_ratio, user_data)
        
        keyboard = []
        for platform in suggested_platforms:
            emoji = self._get_platform_emoji(platform)
            keyboard.append([InlineKeyboardButton(f"{emoji} {platform.title()}", 
                                                 callback_data=f"publish_{platform}_{video.file_id}")])
        
        keyboard.append([InlineKeyboardButton("🎯 All Platforms", callback_data=f"publish_all_{video.file_id}")])
        keyboard.append([InlineKeyboardButton("⚙️ Custom Setup", callback_data=f"custom_{video.file_id}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        analysis_text = f"""
📹 Video Analysis:
Duration: {duration}s
Aspect: {aspect_ratio:.2f}
Size: {video.file_size / 1024 / 1024:.1f}MB

✨ Suggested platforms based on your content:
        """
        
        await update.message.reply_text(analysis_text, reply_markup=reply_markup)
    
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle photo content"""
        user_id = update.effective_user.id
        user_data = self.get_user_data(user_id)
        
        photo = update.message.photo[-1]  # Get highest resolution
        caption = update.message.caption or ""
        
        keyboard = [
            [InlineKeyboardButton("📸 IG Post", callback_data=f"photo_ig_post_{photo.file_id}")],
            [InlineKeyboardButton("📱 IG Story", callback_data=f"photo_ig_story_{photo.file_id}")],
            [InlineKeyboardButton("🐦 Twitter", callback_data=f"photo_twitter_{photo.file_id}")],
            [InlineKeyboardButton("💼 LinkedIn", callback_data=f"photo_linkedin_{photo.file_id}")],
            [InlineKeyboardButton("🎯 All Platforms", callback_data=f"photo_all_{photo.file_id}")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"📸 Photo received!\nCaption: {caption[:50]}...\n\nWhere should I publish this?",
            reply_markup=reply_markup
        )
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text content"""
        text = update.message.text
        user_id = update.effective_user.id
        
        text_length = len(text)
        
        # Analyze text and suggest formats
        if text_length <= 280:
            formats = ["Twitter Post", "IG Story", "LinkedIn Update"]
        elif text_length <= 1000:
            formats = ["Twitter Thread", "IG Caption", "LinkedIn Post"]
        else:
            formats = ["LinkedIn Article", "Twitter Thread", "Blog Post"]
        
        keyboard = []
        for fmt in formats:
            keyboard.append([InlineKeyboardButton(f"📝 {fmt}", 
                                                 callback_data=f"text_{fmt.lower().replace(' ', '_')}_{hash(text) % 10000}")])
        
        keyboard.append([InlineKeyboardButton("🎨 Create Visual", callback_data=f"text_visual_{hash(text) % 10000}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"📝 Text Analysis:\nLength: {text_length} chars\n\nSuggested formats:",
            reply_markup=reply_markup
        )
    
    async def handle_audio(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle audio content"""
        audio = update.message.audio or update.message.voice
        
        keyboard = [
            [InlineKeyboardButton("🎵 Audiogram", callback_data=f"audio_audiogram_{audio.file_id}")],
            [InlineKeyboardButton("📊 Waveform Visual", callback_data=f"audio_waveform_{audio.file_id}")],
            [InlineKeyboardButton("📝 Transcribe", callback_data=f"audio_transcribe_{audio.file_id}")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        duration = getattr(audio, 'duration', 0)
        await update.message.reply_text(
            f"🎵 Audio received!\nDuration: {duration}s\n\nWhat should I create?",
            reply_markup=reply_markup
        )
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle document uploads"""
        document = update.message.document
        file_name = document.file_name
        mime_type = document.mime_type
        
        await update.message.reply_text(
            f"📄 Document: {file_name}\nType: {mime_type}\n\n"
            "I can process images, videos, and text files. Other formats coming soon!"
        )
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline keyboard callbacks"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data.startswith("setup_"):
            await self._handle_setup_callback(query)
        elif data.startswith("publish_"):
            await self._handle_publish_callback(query)
        elif data.startswith("photo_"):
            await self._handle_photo_callback(query)
        elif data.startswith("text_"):
            await self._handle_text_callback(query)
        elif data.startswith("audio_"):
            await self._handle_audio_callback(query)
    
    async def _handle_setup_callback(self, query):
        """Handle setup callbacks"""
        if query.data == "setup_profile":
            await query.edit_message_text(
                "🔧 Profile Setup\n\nUse these commands:\n"
                "/profile - Set language, timezone, brand\n"
                "/platforms - Connect social accounts\n"
                "/templates - Manage templates"
            )
        elif query.data == "setup_platforms":
            await query.edit_message_text(
                "🔗 Platform Connection\n\n"
                "Connect your accounts:\n"
                "• YouTube\n• TikTok\n• Instagram\n• Twitter\n• LinkedIn\n\n"
                "Use /platforms command for details"
            )
    
    async def _handle_publish_callback(self, query):
        """Handle video publish callbacks"""
        parts = query.data.split("_")
        action = parts[1]  # platform or 'all'
        file_id = parts[2]
        
        if action == "all":
            await query.edit_message_text(
                f"🚀 Publishing to all connected platforms...\n\n"
                f"Video ID: {file_id}\n"
                f"Status: Processing..."
            )
            # TODO: Implement actual publishing
        else:
            await query.edit_message_text(
                f"📤 Publishing to {action.title()}...\n\n"
                f"Video ID: {file_id}\n"
                f"Status: Processing..."
            )
    
    async def _handle_photo_callback(self, query):
        """Handle photo callbacks"""
        await query.edit_message_text("📸 Processing photo... Feature coming soon!")
    
    async def _handle_text_callback(self, query):
        """Handle text callbacks"""
        await query.edit_message_text("📝 Processing text... Feature coming soon!")
    
    async def _handle_audio_callback(self, query):
        """Handle audio callbacks"""
        await query.edit_message_text("🎵 Processing audio... Feature coming soon!")
    
    def _suggest_platforms_for_video(self, duration: int, aspect_ratio: float, user_data: dict) -> list:
        """Suggest platforms based on video characteristics"""
        suggestions = []
        
        # Short vertical videos
        if duration <= 60 and aspect_ratio < 1:
            suggestions.extend(["tiktok", "youtube", "instagram"])
        
        # Longer videos
        elif duration > 60:
            suggestions.extend(["youtube", "linkedin"])
        
        # Square/horizontal videos
        elif aspect_ratio >= 1:
            suggestions.extend(["instagram", "twitter", "linkedin"])
        
        # Filter based on user's connected platforms
        connected = [p for p, config in user_data.get("platforms", {}).items() 
                    if config.get("enabled", False)]
        
        return [p for p in suggestions if p in connected] or ["youtube", "tiktok", "instagram"]
    
    def _get_platform_emoji(self, platform: str) -> str:
        """Get emoji for platform"""
        emojis = {
            "youtube": "📺",
            "tiktok": "🎵",
            "instagram": "📸",
            "twitter": "🐦",
            "linkedin": "💼"
        }
        return emojis.get(platform, "📱")
    
    async def profile_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Profile configuration"""
        await update.message.reply_text("🔧 Profile configuration coming soon!")
    
    async def platforms_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Platform connection"""
        await update.message.reply_text("🔗 Platform connection coming soon!")
    
    async def templates_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Template management"""
        await update.message.reply_text("📚 Template management coming soon!")
    
    async def schedule_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Schedule management"""
        await update.message.reply_text("⏰ Schedule management coming soon!")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Help message"""
        help_text = """
🎬 ClipFlow Bot Commands:

📹 Content:
• Send video → Auto-publish to platforms
• Send photo → Create posts/stories  
• Send text → Generate threads/articles
• Send audio → Create audiograms

⚙️ Setup:
/profile - Configure language, brand
/platforms - Connect social accounts
/templates - Manage content templates
/schedule - Set posting times

🎯 Just send any content and I'll handle the rest!
        """
        await update.message.reply_text(help_text)
    
    def run(self):
        """Start the bot"""
        logger.info("Starting ClipFlow Bot...")
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)

def main():
    # Get bot token from environment
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("Error: TELEGRAM_BOT_TOKEN environment variable not set")
        return
    
    bot = ClipFlowBot(token)
    bot.run()

if __name__ == "__main__":
    main()