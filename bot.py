import os
import threading
import logging
from flask import Flask
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CommandHandler
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# Initialize bot application
app = Application.builder().token(TOKEN).build()

# Dictionary to store file sequence tracking
file_tracker = {}
processed_files = set()  # Store processed file IDs to prevent duplicates

# Setup Flask server (for Render free deployment)
server = Flask(__name__)

@server.route("/")
def home():
    return "Bot is running!"

# Function to check missing files
def find_missing_files(channel_id):
    if not file_tracker.get(channel_id):
        return []
    
    sequence = sorted(file_tracker[channel_id])
    missing = []
    for i in range(sequence[0], sequence[-1] + 1):
        if i not in sequence:
            missing.append(i)
    
    return missing

# Handle "/start" command
async def start(update: Update, context):
    await update.message.reply_text("Hello! Send me files, and I'll forward them in order!")

# Handle files from users
async def handle_file(update: Update, context):
    file = update.message.document
    user_id = update.message.from_user.id
    caption = update.message.caption or ""
    
    # Extract file number and target channel/group from caption
    parts = caption.split()
    if len(parts) < 2:
        await update.message.reply_text("❌ Please use this format:\n`File Number: 0001\nSend to: @channelname`", parse_mode="Markdown")
        return
    
    try:
        file_number = int(parts[0])  # Extract file number
    except ValueError:
        await update.message.reply_text("❌ Invalid file number format! Use numbers like `0001` or `002`.")
        return
    
    channel_id = parts[1]  # Extract channel or group ID

    # Initialize tracking for this channel if not exists
    if channel_id not in file_tracker:
        file_tracker[channel_id] = set()

    # Check for duplicate files
    if file.file_unique_id in processed_files:
        await update.message.reply_text(f"🚫 Duplicate file detected! File {file_number} already sent.")
        return
    
    # Check for missing files
    file_tracker[channel_id].add(file_number)
    missing_files = find_missing_files(channel_id)

    if missing_files:
        await update.message.reply_text(f"⚠️ Missing files detected: {missing_files}. Please upload them first.")
        return

    # Forward file to target channel/group
    await context.bot.send_document(chat_id=channel_id, document=file.file_id, caption=f"File {file_number}")
    processed_files.add(file.file_unique_id)
    
    await update.message.reply_text(f"✅ File {file_number} received and forwarded to {channel_id}.")

# Add command & message handlers
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.Document.ALL, handle_file))

# Run Flask in a separate thread
def run_flask():
    server.run(host="0.0.0.0", port=10000)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    print("Bot is running...")
    app.run_polling()
