import os
import telebot

# קח את הטוקן מה־Environment Variables
BOT_TOKEN = os.environ.get("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable not set")

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(func=lambda m: True)
def get_chat_id(message):
    if message.forward_from_chat:
        print("Chat ID:", message.forward_from_chat.id)
    else:
        print("This is not a forwarded message.")

bot.polling()
