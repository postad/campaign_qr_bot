import telebot

# Replace this with your actual bot token
bot = telebot.TeleBot("YOUR_BOT_TOKEN")

@bot.message_handler(func=lambda m: True)
def get_chat_id(message):
    if message.forward_from_chat:
        print("Chat ID:", message.forward_from_chat.id)
    else:
        print("⚠️ This is not a forwarded message.")

print("🤖 Bot is running. Forward a message from your channel to this bot.")
bot.polling()
