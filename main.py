# main.py (modified for webhooks)
import os
from telegram.ext import ApplicationBuilder
from campaign_qr_bot import conv_handler

# Get the bot token and public URL from environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

def main():
    """Starts the bot with a webhook."""
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN environment variable is not set!")
        return
    if not WEBHOOK_URL:
        print("Error: WEBHOOK_URL environment variable is not set!")
        return

    # Build the application
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Add the conversation handler
    app.add_handler(conv_handler)

    # Set up the webhook
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        url_path=BOT_TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}"
    )

if __name__ == "__main__":
    main()
