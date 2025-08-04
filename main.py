import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from campaign_qr_bot import conv_handler

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main() -> None:
    """Start the bot."""
    PORT = int(os.environ.get("PORT", 8000))
    TOKEN = os.getenv("BOT_TOKEN")
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")

    if not all([TOKEN, WEBHOOK_URL]):
        logger.error("Required environment variables are not set.")
        return

    application = Application.builder().token(TOKEN).build()

    # Add the conversation handler to the application
    application.add_handler(conv_handler)
    
    # Run the bot with webhook
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{TOKEN}"
    )

if __name__ == "__main__":
    main()
