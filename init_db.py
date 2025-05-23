from app import app, db
from models import Policy, Notification

# Use the application context
with app.app_context():
    # Create all tables
    print("Creating database tables...")
    db.create_all()
    
    print("Database initialized successfully!")
