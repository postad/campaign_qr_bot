# main.py
import os
from telegram.ext import ApplicationBuilder, ConversationHandler, CommandHandler   
from campaign_qr_bot import conv_handler

# Get the bot token from the environment variable
BOT_TOKEN = os.getenv("BOT_TOKEN")

def main():
    """Starts the bot."""
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN environment variable is not set!")
        return

    # Build the application
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Add the ConversationHandler for the main bot flow
    app.add_handler(conv_handler)
    
    # Add the new CommandHandler for viewing private posts
    app.add_handler(CommandHandler("view_post", view_post_command_handler))

    # Set up the webhook
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        url_path=BOT_TOKEN,
        webhook_url=f"{os.getenv('WEBHOOK_URL')}/{BOT_TOKEN}"
    )

if __name__ == "__main__":
    main()
