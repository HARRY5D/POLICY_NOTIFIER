from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Initialize SQLAlchemy
db = SQLAlchemy()

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    policy_id = db.Column(db.Integer, db.ForeignKey('policy.id'), nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    subject = db.Column(db.String(200), nullable=False)
    recipient = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # 'success' or 'failed'
    
    def __repr__(self):
        return f"Notification(Policy #{self.policy_id}, sent at {self.sent_at}, status: {self.status})"

class Policy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    details = db.Column(db.Text, nullable=True)
    email = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notification_hour = db.Column(db.Integer, default=9)  # Default to 9 AM
    notification_minute = db.Column(db.Integer, default=0)  # Default to 0 minutes
    last_notified = db.Column(db.DateTime, nullable=True)  # When the last notification was sent
    
    def __repr__(self):
        return f"Policy('{self.name}', due on {self.due_date})"
        
    @property
    def notification_time_str(self):
        """Return the notification time as a formatted string."""
        hour = self.notification_hour
        minute = self.notification_minute
        am_pm = "AM" if hour < 12 else "PM"
        
        # Convert to 12-hour format
        if hour == 0:
            hour = 12
        elif hour > 12:
            hour -= 12
            
        return f"{hour}:{minute:02d} {am_pm}"
