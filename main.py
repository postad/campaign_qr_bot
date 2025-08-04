# main.py (now the main runner)
from telegram.ext import ApplicationBuilder, CommandHandler
import os
from campaign_qr_bot import conv_handler # Import the handler

BOT_TOKEN = os.getenv("BOT_TOKEN")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Add the conversation handler from the other file
    app.add_handler(conv_handler)

    app.run_polling()

if __name__ == "__main__":
    main()
