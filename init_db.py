import sqlite3

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

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
