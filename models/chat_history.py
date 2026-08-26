import sqlite3
import os
from datetime import datetime


# --------------------------------
# Project Root
# --------------------------------
project_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

# Database will be created in project root
db_path = os.path.join(
    project_root,
    "chat_history.db"
)


# --------------------------------
# Create Database
# --------------------------------
def create_history_database():

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# --------------------------------
# Save Message
# --------------------------------
def save_message(role, content):

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO chat_history
        (role, content, timestamp)
        VALUES (?, ?, ?)
        """,
        (
            role,
            content,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    )

    conn.commit()
    conn.close()


# --------------------------------
# Load Previous Messages
# --------------------------------
def load_history():

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT role, content
        FROM chat_history
        ORDER BY id ASC
    """)

    rows = cursor.fetchall()

    conn.close()

    return [
        {
            "role": role,
            "content": content
        }
        for role, content in rows
    ]


# --------------------------------
# Clear History
# --------------------------------
def clear_history():

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM chat_history"
    )

    conn.commit()
    conn.close()