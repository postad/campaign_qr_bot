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
    """Publishes the post, generates a QR code and a shareable command, and ends the conversation."""
    if update.message.text.lower() != 'yes':
        await update.message.reply_text("❌ Post canceled.")
        del user_data_store[update.effective_chat.id]
        return ConversationHandler.END

    data = user_data_store[update.effective_chat.id]

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

    # We now generate a special command that the user can send to the bot.
    post_command = f"/view_post_{sent_msg.message_id}"
    shareable_text = (
        "Here's your shareable command. Instruct your audience to send this "
        "command directly to this bot to view the post."
    )

    # We will generate a QR code for this command
    img = qrcode.make(post_command)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
        img.save(tmpfile.name)
        with open(tmpfile.name, 'rb') as qr_code_file:
            await update.message.reply_photo(photo=qr_code_file, caption=f"Here's your QR code.\nCommand: `{post_command}`")
        os.remove(tmpfile.name)

    await update.message.reply_text(f"✅ Done!\n{shareable_text}")
    del user_data_store[update.effective_chat.id]
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancels the conversation."""
    await update.message.reply_text("❌ Canceled.")
    if update.effective_chat.id in user_data_store:
        del user_data_store[update.effective_chat.id]
    return ConversationHandler.END

async def view_post_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the custom command to view a specific post."""
    command_text = update.message.text
    try:
        # Extract the message_id from the command, e.g., '/view_post_123'
        message_id = int(command_text.split('_')[-1])
        campaign_channel_id = os.getenv("CAMPAIGN_CHANNEL")

        if not campaign_channel_id:
            await update.message.reply_text("❌ Configuration error: CAMPAIGN_CHANNEL (ID) not set.")
            return

        # Use copy_message to forward the post to the user
        await context.bot.copy_message(
            chat_id=update.effective_chat.id,
            from_chat_id=campaign_channel_id,
            message_id=message_id
        )
    except (ValueError, IndexError):
        await update.message.reply_text("Invalid command format. Please use the command provided to you.")
    except Exception as e:
        await update.message.reply_text(f"An error occurred while fetching the post: {e}")

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
