import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# --- Environment Variables ---
# Make sure to create a .env file with your TELEGRAM_BOT_TOKEN
# Example: TELEGRAM_BOT_TOKEN="123456:ABC-DEF1234567890"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a welcome message when the /start command is issued."""
    await update.message.reply_text(
        "Welcome to ClipFlow! 🚀\n\n"
        "I can help you automate your content creation and publishing. "
        "Send me any content (video, photo, text, audio) and I'll do the rest.\n\n"
        "Here are some commands to get you started:\n"
        "/profile - Configure your language, timezone, and brand settings\n"
        "/platforms - Connect your social media accounts\n"
        "/schedule - View and manage your scheduled posts\n"
        "/help - Show all available commands"
    )

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /profile command."""
    await update.message.reply_text("This is the /profile command. (Not yet implemented)")

async def preset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /preset command."""
    await update.message.reply_text("This is the /preset command. (Not yet implemented)")

async def brand(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /brand command."""
    await update.message.reply_text("This is the /brand command. (Not yet implemented)")

async def schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /schedule command."""
    await update.message.reply_text("This is the /schedule command. (Not yet implemented)")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /status command."""
    await update.message.reply_text("This is the /status command. (Not yet implemented)")

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles incoming media files (video, photo, audio, document)."""
    user = update.effective_user
    if update.message.video:
        file_type = "video"
        file_id = update.message.video.file_id
    elif update.message.photo:
        file_type = "photo"
        file_id = update.message.photo[-1].file_id  # Get the largest photo
    elif update.message.audio:
        file_type = "audio"
        file_id = update.message.audio.file_id
    elif update.message.document:
        file_type = "document"
        file_id = update.message.document.file_id
    else:
        file_type = "unknown"
        file_id = "N/A"

    await update.message.reply_text(
        f"Received {file_type} from {user.first_name}. File ID: {file_id}\n"
        "Media processing is not yet implemented."
    )

def main():
    """Starts the bot."""
    if not TELEGRAM_BOT_TOKEN:
        print("TELEGRAM_BOT_TOKEN not found. Please create a .env file with your token.")
        return

    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Command Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("profile", profile))
    application.add_handler(CommandHandler("preset", preset))
    application.add_handler(CommandHandler("brand", brand))
    application.add_handler(CommandHandler("schedule", schedule))
    application.add_handler(CommandHandler("status", status))

    # Message Handler for media
    application.add_handler(MessageHandler(
        filters.PHOTO | filters.VIDEO | filters.AUDIO | filters.Document.ALL,
        handle_media
    ))

    print("Bot started...")
    application.run_polling()

if __name__ == "__main__":
    main()