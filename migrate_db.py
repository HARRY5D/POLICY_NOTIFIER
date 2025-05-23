"""
Migration script to add missing columns to policy table
"""
import sqlite3
import os

def migrate_database():
    """Add missing columns to the policy table."""
    print("Starting database migration...")
    
    # Connect to the database
    db_path = os.path.join(os.path.dirname(__file__), 'policies.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if notification_hour column exists
        cursor.execute("PRAGMA table_info(policy)")
        columns = [col[1] for col in cursor.fetchall()]
        
        columns_to_add = []
        if 'notification_hour' not in columns:
            columns_to_add.append(("notification_hour", "INTEGER DEFAULT 9"))
        
        if 'notification_minute' not in columns:
            columns_to_add.append(("notification_minute", "INTEGER DEFAULT 0"))
        
        if 'last_notified' not in columns:
            columns_to_add.append(("last_notified", "DATETIME"))
        
        # Add the missing columns
        for column_name, column_type in columns_to_add:
            try:
                cursor.execute(f"ALTER TABLE policy ADD COLUMN {column_name} {column_type}")
                print(f"Successfully added column: {column_name}")
            except sqlite3.OperationalError as e:
                print(f"Error adding column {column_name}: {str(e)}")
        
        conn.commit()
        print("Database migration completed successfully.")
    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
