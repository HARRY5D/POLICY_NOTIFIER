from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, session
from datetime import datetime, date, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from forms import PolicyForm
from db import init_db, Policy, Notification

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-dev-key')

# Setup SMTP configuration
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
SMTP_USERNAME = os.environ.get('SMTP_USERNAME', '')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
EMAIL_SENDER = os.environ.get('EMAIL_SENDER', '')
EMAIL_RECIPIENT = os.environ.get('EMAIL_RECIPIENT', '')

def send_email(subject, body, recipient):
    """Send an email notification using SMTP."""
    if not all([SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, EMAIL_SENDER]):
        app.logger.error("SMTP configuration is incomplete. Email not sent.")
        return False
    
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = recipient
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'html'))
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  # Secure the connection
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
            
        app.logger.info(f"Email notification sent to {recipient}")
        return True
    except Exception as e:
        app.logger.error(f"Failed to send email: {str(e)}")
        return False

def check_due_policies():
    """Check for policies due today and send notifications based on their scheduled time."""
    today = date.today().isoformat()
    now = datetime.now()
    current_hour = now.hour
    current_minute = now.minute
    
    app.logger.info(f"Checking for policies due on {today} at {current_hour:02d}:{current_minute:02d}")
    
    # Find policies due today with notification time matching current time (within a 5-minute window)
    due_policies = Policy.get_due_today(today, current_hour, 5)
    
    if due_policies:
        app.logger.info(f"Found {len(due_policies)} policies due for notification")
    
    for policy in due_policies:
        subject = f"Policy Reminder: {policy['name']}"
        body = f"""
        <html>
          <body>
            <h2>Policy Reminder</h2>
            <p>This is a reminder that the following policy is due today:</p>
            <p><strong>Policy Name:</strong> {policy['name']}</p>
            <p><strong>Due Date:</strong> {policy['due_date']}</p>
            <p><strong>Details:</strong> {policy['details'] or 'No details provided'}</p>
          </body>
        </html>
        """
        # Send email to the policy's email recipient
        success = send_email(subject, body, policy['email'])
        
        # Record the notification
        Notification.create(
            policy_id=policy['id'],
            subject=subject,
            recipient=policy['email'],
            status='success' if success else 'failed'
        )
        
        # Update the policy's last_notified time
        if success:
            Policy.update_last_notified(policy['id'], datetime.now().isoformat())
            
        if success:
            app.logger.info(f"Email sent for policy: {policy['name']}")
        else:
            app.logger.error(f"Failed to send email for policy: {policy['name']}")

# Initialize scheduler to run every minute to check for due policies
scheduler = BackgroundScheduler()
scheduler.add_job(
    check_due_policies,
    trigger='interval',
    minutes=1,
    id='check_policies',
    name='Check for policies due today',
    replace_existing=True
)

# Routes
@app.route('/')
def index():
    # Get all policies as raw database rows
    raw_policies = Policy.get_all()    # Convert SQLite rows to dictionaries and parse dates
    policies = []
    for policy in raw_policies:
        policy_dict = dict(policy)
        policy_dict['due_date'] = datetime.strptime(policy_dict['due_date'], '%Y-%m-%d').date()
        
        # Convert created_at timestamp to datetime object if it exists and is not None
        if policy_dict.get('created_at'):
            try:
                policy_dict['created_at'] = datetime.strptime(policy_dict['created_at'], '%Y-%m-%d %H:%M:%S')
            except (ValueError, TypeError):
                # If format doesn't match, just keep as string
                pass
        else:
            policy_dict['created_at'] = None
        
        # Convert last_notified timestamp to datetime object if it exists and is not None
        if policy_dict.get('last_notified'):
            try:
                policy_dict['last_notified'] = datetime.strptime(policy_dict['last_notified'], '%Y-%m-%d %H:%M:%S')
            except (ValueError, TypeError):
                # If format doesn't match, just keep as string
                pass
        else:
            policy_dict['last_notified'] = None
                
        policies.append(policy_dict)
    
    today = date.today()
    return render_template('index.html', policies=policies, today=today)

@app.route('/add', methods=['GET', 'POST'])
def add_policy():
    form = PolicyForm()
    if form.validate_on_submit():
        Policy.create(
            name=form.name.data,
            due_date=form.due_date.data.isoformat(),
            details=form.details.data,
            email=form.email.data,
            notification_hour=form.notification_hour.data,
            notification_minute=form.notification_minute.data
        )
        flash('Policy has been added successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('add_policy.html', form=form, title="Add New Policy")

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_policy(id):
    policy = Policy.get_by_id(id)
    if not policy:
        flash('Policy not found!', 'danger')
        return redirect(url_for('index'))
    
    # Format the date for the form field
    form = PolicyForm()
    
    if request.method == 'GET':
        form.name.data = policy['name']
        form.due_date.data = datetime.strptime(policy['due_date'], '%Y-%m-%d').date()
        form.details.data = policy['details']
        form.email.data = policy['email']
        form.notification_hour.data = policy['notification_hour']
        form.notification_minute.data = policy['notification_minute']
    
    if form.validate_on_submit():
        Policy.update(
            id=id,
            name=form.name.data,
            due_date=form.due_date.data.isoformat(),
            details=form.details.data,
            email=form.email.data,
            notification_hour=form.notification_hour.data,
            notification_minute=form.notification_minute.data
        )
        flash('Policy has been updated!', 'success')
        return redirect(url_for('index'))
    
    return render_template('add_policy.html', form=form, title="Edit Policy")

@app.route('/delete/<int:id>')
def delete_policy(id):
    Policy.delete(id)
    flash('Policy has been deleted!', 'success')
    return redirect(url_for('index'))

@app.route('/send_notification/<int:id>')
def send_notification_now(id):
    """Manually send a notification for a policy immediately."""
    policy = Policy.get_by_id(id)
    if not policy:
        flash('Policy not found!', 'danger')
        return redirect(url_for('index'))
    
    subject = f"Policy Reminder: {policy['name']}"
    body = f"""
    <html>
      <body>
        <h2>Policy Reminder</h2>
        <p>This is a manual reminder about the following policy:</p>
        <p><strong>Policy Name:</strong> {policy['name']}</p>
        <p><strong>Due Date:</strong> {policy['due_date']}</p>
        <p><strong>Details:</strong> {policy['details'] or 'No additional details provided.'}</p>
      </body>
    </html>
    """
    
    # Send email
    success = send_email(subject, body, policy['email'])
    
    # Record the notification
    Notification.create(
        policy_id=policy['id'],
        subject=subject,
        recipient=policy['email'],
        status='success' if success else 'failed'
    )
    
    if success:
        Policy.update_last_notified(policy['id'], datetime.now().isoformat())
        flash('Notification sent successfully!', 'success')
    else:
        flash('Failed to send notification. Please check your SMTP configuration.', 'danger')
    
    return redirect(url_for('index'))

@app.route('/test_email', methods=['POST'])
def test_email():
    """Test the email configuration by sending a test email."""
    recipient = request.form.get('email', EMAIL_RECIPIENT)
    subject = "Policy Notifier - Test Email"
    body = """
    <html>
      <body>
        <h2>Test Email</h2>
        <p>This is a test email from the Policy Notifier system.</p>
        <p>If you received this email, your SMTP configuration is working correctly.</p>
      </body>
    </html>
    """
    
    success = send_email(subject, body, recipient)
    if success:
        flash('Test email sent successfully!', 'success')
    else:
        flash('Failed to send test email. Check your SMTP configuration.', 'danger')
    
    return redirect(url_for('index'))

@app.route('/notifications')
def view_notifications():
    """View email notification history."""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    notifications, total = Notification.get_all(page=page, per_page=per_page)
    
    # Create a simple pagination class to mimic SQLAlchemy's pagination
    class Pagination:
        def __init__(self, items, page, per_page, total):
            self.items = items
            self.page = page
            self.per_page = per_page
            self.total = total
            self.pages = (total + per_page - 1) // per_page
        
        @property
        def has_prev(self):
            return self.page > 1
        
        @property
        def has_next(self):
            return self.page < self.pages
        
        @property
        def prev_num(self):
            return self.page - 1
        
        @property
        def next_num(self):
            return self.page + 1
        
        def iter_pages(self, left_edge=2, left_current=2, right_current=2, right_edge=2):
            last = 0
            for num in range(1, self.pages + 1):
                if num <= left_edge or \
                   (num > self.page - left_current - 1 and num < self.page + right_current) or \
                   num > self.pages - right_edge:
                    if last + 1 != num:
                        yield None
                    yield num
                    last = num
    
    pagination = Pagination(notifications, page, per_page, total)
    
    return render_template('notifications.html', notifications=pagination, title="Notification History")

@app.route('/check_notifications')
def check_notifications():
    """API endpoint to check for new email notifications since the last check."""
    # Get the last time this was checked from session, default to 1 minute ago
    last_check = session.get('last_notification_check', (datetime.now() - timedelta(minutes=1)).isoformat())
    
    # Find notifications sent since the last check
    new_notifications = Notification.get_new_since(last_check)
    
    # Update the last check time
    session['last_notification_check'] = datetime.now().isoformat()
    
    # Return JSON response
    return jsonify({
        'new_notifications': new_notifications > 0,
        'count': new_notifications
    })

if __name__ == '__main__':
    # Initialize the database if it doesn't exist
    init_db()
    
    # Start the scheduler
    scheduler.start()
    
    # Check if we're in development or production mode
    debug_mode = os.environ.get('FLASK_ENV', 'development') == 'development'
    
    # Get port from environment variable or use 5000 as default (for production platforms)
    port = int(os.environ.get('PORT', 5000))
    
    # Run the app
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
