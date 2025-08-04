# main.py
import os
from telegram.ext import ApplicationBuilder
from campaign_qr_bot import conv_handler

# Get the bot token from the environment variable
BOT_TOKEN = os.getenv("BOT_TOKEN")

def main():
    """Starts the bot."""
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN environment variable is not set!")
        return

    # Build the application with explicit timeout settings
    # This can help with persistent 'TimedOut' errors on some networks.
    app = ApplicationBuilder().token(BOT_TOKEN).read_timeout(30).connect_timeout(30).build()

    # Add the conversation handler from the other file
    app.add_handler(conv_handler)

    # Run the bot in polling mode
    app.run_polling()

if __name__ == "__main__":
    main()
