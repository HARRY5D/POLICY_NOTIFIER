import sqlite3
import os
from datetime import datetime

# Connect to the database
db_path = os.path.join('instance', 'policies.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if the columns already exist
cursor.execute("PRAGMA table_info(policy)")
columns = [column[1] for column in cursor.fetchall()]

# Add notification_hour column if it doesn't exist
if 'notification_hour' not in columns:
    print("Adding notification_hour column...")
    cursor.execute("ALTER TABLE policy ADD COLUMN notification_hour INTEGER DEFAULT 9")

# Add notification_minute column if it doesn't exist
if 'notification_minute' not in columns:
    print("Adding notification_minute column...")
    cursor.execute("ALTER TABLE policy ADD COLUMN notification_minute INTEGER DEFAULT 0")

# Add last_notified column if it doesn't exist
if 'last_notified' not in columns:
    print("Adding last_notified column...")
    cursor.execute("ALTER TABLE policy ADD COLUMN last_notified TIMESTAMP")

# Create notifications table if it doesn't exist
print("Creating notifications table if it doesn't exist...")
cursor.execute('''
CREATE TABLE IF NOT EXISTS notification (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    policy_id INTEGER NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    subject TEXT NOT NULL,
    recipient TEXT NOT NULL,
    status TEXT NOT NULL,
    FOREIGN KEY (policy_id) REFERENCES policy (id)
)
''')

# Commit changes and close connection
conn.commit()
print("Database schema updated successfully!")
conn.close()
