import os
import logging
import qrcode
import tempfile
import os
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
    """Publishes the post, generates a QR code and shareable link, and ends the conversation."""
    if update.message.text.lower() != 'yes':
        await update.message.reply_text("❌ Post canceled.")
        del user_data_store[update.effective_chat.id]
        return ConversationHandler.END

    data = user_data_store[update.effective_chat.id]

    campaign_invite_link = os.getenv("CAMPAIGN_INVITE_LINK")
    if not campaign_invite_link:
        await update.message.reply_text("❌ Configuration error: CAMPAIGN_INVITE_LINK not set.")
        del user_data_store[update.effective_chat.id]
        return ConversationHandler.END

    # We still need the channel ID to send the message, but it won't be used for the link.
    campaign_channel_id = os.getenv("CAMPAIGN_CHANNEL")
    if not campaign_channel_id:
        await update.message.reply_text("❌ Configuration error: CAMPAIGN_CHANNEL (ID) not set.")
        del user_data_store[update.effective_chat.id]
        return ConversationHandler.END

    sent_msg = await context.bot.send_photo(
        chat_id=campaign_channel_id,
        photo=data['image_file_id'],
        caption=f"{data['text']}\n{data['link']}"
    )

    # --- START OF CHANGE ---
    # Generate the shareable link using the invite link and message ID
    # The format is 'https://t.me/+invite_hash?comment=message_id'.
    post_url = f"{campaign_invite_link}?comment={sent_msg.message_id}"
    # --- END OF CHANGE ---

    img = qrcode.make(post_url)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
        img.save(tmpfile.name)
        with open(tmpfile.name, 'rb') as qr_code_file:
            await update.message.reply_photo(photo=qr_code_file, caption=f"Here's your QR code.\nURL: {post_url}")
        os.remove(tmpfile.name)

    await update.message.reply_text("✅ Done!")
    del user_data_store[update.effective_chat.id]
    return ConversationHandler.END

    # --- START OF CHANGE ---
    # Generate the private link and QR code
    # The numerical ID needs to be formatted for a private channel deep-link.
    # The format is 't.me/c/ID_WITHOUT_100/MESSAGE_ID'.
    # We remove the '-100' prefix from the numerical ID.
    if campaign_channel.startswith('-100'):
        # For a private channel, remove the '-100' prefix
        # Example: '-1002828754822' becomes '2828754822'
        channel_id_for_link = campaign_channel[4:]
        post_url = f"https://t.me/c/{channel_id_for_link}/{sent_msg.message_id}"
    else:
        # This is a fallback for public channels (though not your use case)
        # We assume it's a username and remove the '@'
        channel_username_for_link = campaign_channel[1:]
        post_url = f"https://t.me/{channel_username_for_link}/{sent_msg.message_id}"
    # --- END OF CHANGE ---

    img = qrcode.make(post_url)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
        img.save(tmpfile.name)
        with open(tmpfile.name, 'rb') as qr_code_file:
            await update.message.reply_photo(photo=qr_code_file, caption=f"Here's your QR code.\nURL: {post_url}")
        os.remove(tmpfile.name)

    await update.message.reply_text("✅ Done!")
    del user_data_store[update.effective_chat.id]
    return ConversationHandler.END

    data = user_data_store[update.effective_chat.id]

    # Send the post to the hidden campaign channel
    campaign_channel = os.getenv("CAMPAIGN_CHANNEL")
    if not campaign_channel:
        await update.message.reply_text("❌ Configuration error: CAMPAIGN_CHANNEL not set.")
        del user_data_store[update.effective_chat.id]
        return ConversationHandler.END

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
        with open(tmpfile.name, 'rb') as qr_code_file:
            await update.message.reply_photo(photo=qr_code_file, caption=f"Here's your QR code.\nURL: {post_url}")
        os.remove(tmpfile.name) # Clean up the temporary file

    await update.message.reply_text("✅ Done!")
    del user_data_store[update.effective_chat.id] # Clean up data
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancels the conversation."""
    await update.message.reply_text("❌ Canceled.")
    if update.effective_chat.id in user_data_store:
        del user_data_store[update.effective_chat.id] # Clean up data
    return ConversationHandler.END

# Define the ConversationHandler for use in the main script
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
