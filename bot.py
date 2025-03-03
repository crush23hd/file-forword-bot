import os
import sqlite3
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Load environment variables
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))  # Admin user ID

# Database setup
DB_FILE = "bot_data.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id TEXT UNIQUE,
            file_name TEXT,
            file_number INTEGER
        )
    """)
    conn.commit()
    conn.close()

# Initialize database
init_db()

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Store user channel/group selections
user_destinations = {}

async def start(update: Update, context: CallbackContext):
    """ Start command """
    await update.message.reply_text("Hello! Send me a file, and I'll forward it to the specified channel/group.")

async def set_destination(update: Update, context: CallbackContext):
    """ Set the destination channel/group """
    if not context.args:
        await update.message.reply_text("Usage: /setchannel <channel_or_group_id>")
        return
    
    chat_id = context.args[0]
    user_id = update.message.from_user.id
    user_destinations[user_id] = chat_id
    await update.message.reply_text(f"Destination set to: {chat_id}")

async def receive_file(update: Update, context: CallbackContext):
    """ Handles file uploads, checks order, and forwards to the selected channel/group """
    user_id = update.message.from_user.id
    destination = user_destinations.get(user_id)

    if not destination:
        await update.message.reply_text("Please set a destination first using /setchannel <channel_id>")
        return

    file = update.message.document or update.message.video or update.message.audio
    if not file:
        await update.message.reply_text("Please send a valid file.")
        return

    file_id = file.file_id
    file_name = file.file_name if hasattr(file, 'file_name') else "Unknown"

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Check for duplicate file
    cursor.execute("SELECT file_id FROM files WHERE file_id = ?", (file_id,))
    if cursor.fetchone():
        await update.message.reply_text("Duplicate file detected. Skipping upload.")
        conn.close()
        return

    # Determine next file number
    cursor.execute("SELECT COALESCE(MAX(file_number), 0) FROM files")
    last_number = cursor.fetchone()[0]
    next_number = last_number + 1
    formatted_number = f"{next_number:04d}"  # Format as 0001, 0002, etc.

    # Save file info to DB
    cursor.execute("INSERT INTO files (file_id, file_name, file_number) VALUES (?, ?, ?)", 
                   (file_id, file_name, next_number))
    conn.commit()
    conn.close()

    # Forward file to the destination
    await context.bot.send_document(chat_id=destination, document=file_id, caption=f"File {formatted_number}: {file_name}")

    await update.message.reply_text(f"File {formatted_number} forwarded successfully!")

async def check_missing(update: Update, context: CallbackContext):
    """ Check for missing files in the sequence """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT file_number FROM files ORDER BY file_number")
    numbers = [row[0] for row in cursor.fetchall()]
    conn.close()

    missing = [n for n in range(1, max(numbers, default=1) + 1) if n not in numbers]
    
    if missing:
        await update.message.reply_text(f"Missing file numbers: {', '.join(map(str, missing))}")
    else:
        await update.message.reply_text("No missing files detected.")

def main():
    """ Main function to start the bot """
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setchannel", set_destination))
    app.add_handler(CommandHandler("checkmissing", check_missing))
    app.add_handler(MessageHandler(filters.ALL, receive_file))

    logger.info("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
