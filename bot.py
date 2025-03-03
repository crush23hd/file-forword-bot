import os
import re
import logging
import hashlib
import sqlite3
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CommandHandler, CallbackContext

# Load environment variables
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# Set up logging
logging.basicConfig(level=logging.INFO)

# Database setup
DB_FILE = "bot_data.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS channels (
            user_id INTEGER PRIMARY KEY,
            chat_id TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS files (
            user_id INTEGER,
            file_number INTEGER UNIQUE,
            file_name TEXT,
            PRIMARY KEY (user_id, file_number)
        )
    """)
    conn.commit()
    conn.close()

init_db()

# Store received file hashes to prevent duplicates
received_files = {}

# Extract number from filename (e.g., 0001.pdf → 0001)
def extract_number(file_name):
    match = re.search(r"(\d+)", file_name)
    return int(match.group(1)) if match else None

# Command: Set Channel/Group ID
async def set_channel(update: Update, context: CallbackContext):
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /setchannel <channel_id>")
        return
   
