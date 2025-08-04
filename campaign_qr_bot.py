import os
import logging
import qrcode
import tempfile
from telegram import Update
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, filters, ContextTypes

# States
IMAGE, TEXT, LINK, CONFIRM = range(4)

# Store user inputs temporarily
user_data_store = {}

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Starts the conversation and asks for the image."""
    await update.message.reply_text("Please upload the image for the post.")
    return IMAGE

async def get_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stores the image and asks for the text."""
    photo = update.message.photo[-1]
    file = await photo.get_file()
    user_data_store[update.effective_chat.id] = {"image_file_id": file.file_id}
    await update.message.reply_text("Image received. Now send the text for the post (with emojis if needed).")
    return TEXT

async def get_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stores the text and asks for the link."""
    user_data_store[update.effective_chat.id]["text"] = update.message.text
    await update.message.reply_text("Now send the link (it will appear as-is in the post).")
    return LINK

async def get_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stores the link, shows a preview, and asks for confirmation."""
    user_data_store[update.effective_chat.id]["link"] = update.message.text
    data = user_data_store[update.effective_chat.id]
    preview = f"{data['text']}\n{data['link']}"
    await update.message.reply_photo(photo=data['image_file_id'], caption=preview)
    await update.message.reply_text("✅ This is your post preview. Type 'yes' to confirm and publish.")
    return CONFIRM

async def confirm_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Publishes the post and then edits it to only show a link."""
    if update.message.text.lower() != 'yes':
        await update.message.reply_text("❌ Post canceled.")
        del user_data_store[update.effective_chat.id]
        return ConversationHandler.END

    data = user_data_store[update.effective_chat.id]
    
    # Assume CAMPAIGN_CHANNEL is a public channel username like '@my_public_channel'
    campaign_channel_username = os.getenv("CAMPAIGN_CHANNEL")
    if not campaign_channel_username:
        await update.message.reply_text("❌ Configuration error: CAMPAIGN_CHANNEL not set.")
        del user_data_store[update.effective_chat.id]
        return ConversationHandler.END

    # Step 1: Post the full content to the public channel
    sent_msg = await context.bot.send_photo(
        chat_id=campaign_channel_username,
        photo=data['image_file_id'],
        caption=f"{data['text']}\n{data['link']}"
    )

    # Step 2: Get the post's URL
    post_url = f"https://t.me/{campaign_channel_username[1:]}/{sent_msg.message_id}"

    # Step 3: Edit the message to show only the link
    await context.bot.edit_message_caption(
        chat_id=campaign_channel_username,
        message_id=sent_msg.message_id,
        caption=f"Here is the post:\n{post_url}"
    )
    
    # Step 4: Generate a QR code for the public URL
    img = qrcode.make(post_url)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
        img.save(tmpfile.name)
        with open(tmpfile.name, 'rb') as qr_code_file:
            await update.message.reply_photo(photo=qr_code_file, caption=f"Here's your QR code.\nURL: {post_url}")
        os.remove(tmpfile.name)

    await update.message.reply_text("✅ Done!")
    del user_data_store[update.effective_chat.id]
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancels the conversation."""
    await update.message.reply_text("❌ Canceled.")
    if update.effective_chat.id in user_data_store:
        del user_data_store[update.effective_chat.id]
    return ConversationHandler.END

# Define the ConversationHandler for use in the main script
# All functions referenced here must be defined above this line.
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
