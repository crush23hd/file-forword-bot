import os
import logging
import re
import sqlite3
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Load environment variables
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Logging for debugging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# In-memory storage for processed files
processed_files = {}  # {channel_id: set(file_numbers)}

# SQLite Database (Optional)
conn = sqlite3.connect("bot_data.db")
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS files (file_number INTEGER, channel TEXT, UNIQUE(file_number, channel))")
conn.commit()


async def start(update: Update, context: CallbackContext):
    """Handles the /start command"""
    await update.message.reply_text("📂 Send me files with a caption in format: '0001 @channelname'")


async def handle_file(update: Update, context: CallbackContext):
    """Handles file reception and forwards it to the correct channel in sequence"""
    if not update.message.document:
        return

    caption = update.message.caption
    if not caption:
        await update.message.reply_text("⚠️ Please send a caption with the file number and channel name.")
        return

    # Extract file number and channel ID
    match = re.search(r"(\d{1,4})\s+(@?\w+)", caption)
    if not match:
        await update.message.reply_text("❌ Incorrect format! Use: '0001 @channelname'")
        return

    file_number = int(match.group(1))
    channel_id = match.group(2)

    # Ensure the channel tracking exists
    if channel_id not in processed_files:
        processed_files[channel_id] = set()

    # Check for duplicates
    if file_number in processed_files[channel_id]:
        await update.message.reply_text(f"🚫 Duplicate detected! File {file_number} already sent to {channel_id}.")
        return

    # Store file in database
    try:
        c.execute("INSERT INTO files (file_number, channel) VALUES (?, ?)", (file_number, channel_id))
        conn.commit()
    except sqlite3.IntegrityError:
        await update.message.reply_text(f"🚫 Duplicate detected! File {file_number} already in database for {channel_id}.")
        return

    # Identify missing files
    expected_files = set(range(1, file_number))
    sent_files = {row[0] for row in c.execute("SELECT file_number FROM files WHERE channel=?", (channel_id,))}
    missing_files = sorted(expected_files - sent_files)

    # Log missing files but still process
    if missing_files:
        await update.message.reply_text(f"⚠️ Warning: Missing files {missing_files}. Please upload them soon.")

    # Forward file
    file = update.message.document
    await context.bot.send_document(chat_id=channel_id, document=file.file_id, caption=f"📂 File {file_number}")

    # Mark file as processed
    processed_files[channel_id].add(file_number)
    await update.message.reply_text(f"✅ File {file_number} forwarded to {channel_id}!")


def main():
    """Starts the bot"""
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL & filters.Caption, handle_file))

    logger.info("🤖 Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
