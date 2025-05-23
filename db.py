import sqlite3
from datetime import datetime
import os

# Ensure the instance directory exists
os.makedirs('instance', exist_ok=True)

def get_db_connection():
    """Get a connection to the SQLite database."""
    conn = sqlite3.connect('policies.db')
    conn.row_factory = sqlite3.Row  # This enables column access by name
    return conn

def init_db():
    """Initialize the database with the required tables."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create policy table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS policy (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        due_date TEXT NOT NULL,
        details TEXT,
        email TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        notification_hour INTEGER DEFAULT 9,
        notification_minute INTEGER DEFAULT 0,
        last_notified TEXT
    )
    ''')
    
    # Create notification table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS notification (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        policy_id INTEGER NOT NULL,
        sent_at TEXT DEFAULT CURRENT_TIMESTAMP,
        subject TEXT NOT NULL,
        recipient TEXT NOT NULL,
        status TEXT NOT NULL,
        FOREIGN KEY (policy_id) REFERENCES policy (id)
    )
    ''')
    
    conn.commit()
    conn.close()
    
    print("Database initialized successfully!")

# Model-like classes for working with data
class Policy:
    @staticmethod
    def get_all():
        """Get all policies ordered by due date."""
        conn = get_db_connection()
        policies = conn.execute('SELECT * FROM policy ORDER BY due_date').fetchall()
        conn.close()
        return policies
    
    @staticmethod
    def get_by_id(policy_id):
        """Get a policy by its ID."""
        conn = get_db_connection()
        policy = conn.execute('SELECT * FROM policy WHERE id = ?', (policy_id,)).fetchone()
        conn.close()
        return policy
    
    @staticmethod
    def create(name, due_date, details, email, notification_hour=9, notification_minute=0):
        """Create a new policy."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO policy (name, due_date, details, email, notification_hour, notification_minute) VALUES (?, ?, ?, ?, ?, ?)',
            (name, due_date, details, email, notification_hour, notification_minute)
        )
        conn.commit()
        policy_id = cursor.lastrowid
        conn.close()
        return policy_id
    
    @staticmethod
    def update(id, name, due_date, details, email, notification_hour, notification_minute):
        """Update an existing policy."""
        conn = get_db_connection()
        conn.execute(
            'UPDATE policy SET name = ?, due_date = ?, details = ?, email = ?, notification_hour = ?, notification_minute = ? WHERE id = ?',
            (name, due_date, details, email, notification_hour, notification_minute, id)
        )
        conn.commit()
        conn.close()
    
    @staticmethod
    def delete(id):
        """Delete a policy."""
        conn = get_db_connection()
        conn.execute('DELETE FROM policy WHERE id = ?', (id,))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_due_today(today, current_hour, window_minutes):
        """Get policies due today with notification time matching the current hour."""
        conn = get_db_connection()
        current_minute = datetime.now().minute
        lower_minute = max(0, current_minute - window_minutes)
        upper_minute = min(59, current_minute + window_minutes)
        
        policies = conn.execute(
            'SELECT * FROM policy WHERE due_date = ? AND notification_hour = ? AND notification_minute BETWEEN ? AND ?',
            (today, current_hour, lower_minute, upper_minute)
        ).fetchall()
        conn.close()
        return policies
    
    @staticmethod
    def update_last_notified(id, timestamp):
        """Update the last_notified timestamp for a policy."""
        conn = get_db_connection()
        conn.execute(
            'UPDATE policy SET last_notified = ? WHERE id = ?',
            (timestamp, id)
        )
        conn.commit()
        conn.close()

class Notification:
    @staticmethod
    def create(policy_id, subject, recipient, status):
        """Create a new notification record."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO notification (policy_id, subject, recipient, status) VALUES (?, ?, ?, ?)',
            (policy_id, subject, recipient, status)
        )
        conn.commit()
        notification_id = cursor.lastrowid
        conn.close()
        return notification_id
    
    @staticmethod
    def get_all(page=1, per_page=20):
        """Get all notifications with pagination, ordered by sent_at desc."""
        conn = get_db_connection()
        offset = (page - 1) * per_page
        notifications = conn.execute(
            'SELECT * FROM notification ORDER BY sent_at DESC LIMIT ? OFFSET ?',
            (per_page, offset)
        ).fetchall()
        
        # Get total count for pagination
        total = conn.execute('SELECT COUNT(*) FROM notification').fetchone()[0]
        
        conn.close()
        return notifications, total
    
    @staticmethod
    def get_new_since(timestamp):
        """Get count of new successful notifications since a timestamp."""
        conn = get_db_connection()
        count = conn.execute(
            'SELECT COUNT(*) FROM notification WHERE sent_at > ? AND status = ?',
            (timestamp, 'success')
        ).fetchone()[0]
        conn.close()
        return count
