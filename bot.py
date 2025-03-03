import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Set your bot token
BOT_TOKEN = "1193578192:AAFiR7523UP7DgqV-jXtfk1_ZsqJxtUChhI"

# Set the destination chat ID (group/channel where files will be sent)
DESTINATION_CHAT_ID = "YOUR_DESTINATION_CHAT_ID"

# Store sent file IDs to prevent duplicates
sent_files = set()

async def receive_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles receiving a file from a user and forwarding it to a destination chat."""
    if not update.message or not update.message.document:
        logger.warning("No document received.")
        return

    file = update.message.document
    file_id = file.file_id
    file_name = file.file_name

    # Check for duplicate file
    if file_id in sent_files:
        logger.info(f"Duplicate file detected: {file_name} (ID: {file_id})")
        return

    # Determine the next sequence number
    next_number = len(sent_files) + 1
    formatted_number = str(next_number).zfill(4)  # Example: 0001, 0002, etc.

    logger.info(f"Sending file '{file_name}' (ID: {file_id}) to chat ID: {DESTINATION_CHAT_ID}")

    try:
        await context.bot.send_document(
            chat_id=DESTINATION_CHAT_ID,
            document=file_id,
            caption=f"File {formatted_number}: {file_name}",
        )
        sent_files.add(file_id)  # Mark file as sent
        logger.info(f"File '{file_name}' sent successfully!")
    except Exception as e:
        logger.error(f"Error sending file: {e}")

def main():
    """Main function to run the bot."""
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Handle all document uploads
    app.add_handler(MessageHandler(filters.Document.ALL, receive_file))

    logger.info("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
