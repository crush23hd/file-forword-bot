import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if TOKEN:
    print(f"Token loaded successfully: {TOKEN[:10]}********")  # Mask most of the token for security
else:
    print("ERROR: No token found. Check your .env file or environment variables!")
