# campaign_qr_bot.py
import os
import logging
import qrcode
import tempfile
from telegram import Update, InputMediaPhoto
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler, filters, ContextTypes

# States
IMAGE, TEXT, LINK, CONFIRM = range(4)

# Store user inputs temporarily
user_data_store = {}

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Please upload the image for the post")
    return IMAGE

async def get_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await photo.get_file()
    user_data_store[update.effective_chat.id] = {"image_file_id": file.file_id}
    await update.message.reply_text("Image received. Now send the text for the post (with emojis if needed).")
    return TEXT

async def get_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_store[update.effective_chat.id]["text"] = update.message.text
    await update.message.reply_text("Now send the link (it will appear as-is in the post)")
    return LINK

async def get_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_store[update.effective_chat.id]["link"] = update.message.text

    data = user_data_store[update.effective_chat.id]
    preview = f"{data['text']}\n{data['link']}"
    await update.message.reply_photo(photo=data['image_file_id'], caption=preview)
    await update.message.reply_text("✅ This is your post preview. Type 'yes' to confirm and publish.")
    return CONFIRM

async def confirm_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.lower() != 'yes':
        await update.message.reply_text("❌ Post canceled.")
        return ConversationHandler.END

    data = user_data_store[update.effective_chat.id]

    # Send the post to the hidden campaign channel
    campaign_channel = os.getenv("CAMPAIGN_CHANNEL")  # Example: '@PostAd_Campaigns'
    sent_msg = await context.bot.send_photo(
        chat_id=campaign_channel,
        photo=data['image_file_id'],
        caption=f"{data['text']}\n{data['link']}"
    )

    # Generate link and QR code
    post_url = f"https://t.me/{campaign_channel[1:]}/{sent_msg.message_id}"
    img = qrcode.make(post_url)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
        img.save(tmpfile.name)
        await update.message.reply_photo(photo=open(tmpfile.name, 'rb'), caption=f"Here's your QR code.\nURL: {post_url}")

    await update.message.reply_text("✅ Done!")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Canceled")
    return ConversationHandler.END

def main():
    TOKEN = os.getenv("BOT_TOKEN")
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            IMAGE: [MessageHandler(filters.PHOTO, get_image)],
            TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_text)],
            LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_link)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_post)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == '__main__':
    main()
