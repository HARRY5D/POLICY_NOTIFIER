from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, session
from datetime import datetime, date
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-dev-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///policies.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Import db and models after app is created
from models import db, Policy, Notification
from forms import PolicyForm

# Initialize the database with the app
db.init_app(app)

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
    today = date.today()
    now = datetime.now()
    current_hour = now.hour
    current_minute = now.minute
    
    app.logger.info(f"Checking for policies due on {today} at {current_hour:02d}:{current_minute:02d}")
    
    # Use application context to work with database
    with app.app_context():
        # Find policies due today with notification time matching current time (within a 5-minute window)
        due_policies = Policy.query.filter_by(due_date=today).filter(
            Policy.notification_hour == current_hour,
            Policy.notification_minute.between(current_minute - 5, current_minute + 5)
        ).all()
        
        if due_policies:
            app.logger.info(f"Found {len(due_policies)} policies due for notification")
        
        for policy in due_policies:
            subject = f"Policy Reminder: {policy.name}"
            body = f"""
            <html>
              <body>
                <h2>Policy Reminder</h2>
                <p>This is a reminder that the following policy is due today:</p>
                <p><strong>Policy Name:</strong> {policy.name}</p>
                <p><strong>Due Date:</strong> {policy.due_date.strftime('%Y-%m-%d')}</p>
                <p><strong>Details:</strong> {policy.details}</p>
              </body>
            </html>
            """
            # Send email to the policy's email recipient
            success = send_email(subject, body, policy.email)
            
            # Record the notification
            notification = Notification(
                policy_id=policy.id,
                subject=subject,
                recipient=policy.email,
                status='success' if success else 'failed'
            )
            db.session.add(notification)
            
            # Update the policy's last_notified time
            if success:
                policy.last_notified = datetime.now()
                
            db.session.commit()
            
            if success:
                app.logger.info(f"Email sent for policy: {policy.name}")
            else:
                app.logger.error(f"Failed to send email for policy: {policy.name}")

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
    policies = Policy.query.order_by(Policy.due_date).all()
    today = date.today()
    return render_template('index.html', policies=policies, today=today)

@app.route('/add', methods=['GET', 'POST'])
def add_policy():
    form = PolicyForm()
    if form.validate_on_submit():
        policy = Policy(
            name=form.name.data,
            due_date=form.due_date.data,
            details=form.details.data,
            email=form.email.data,
            notification_hour=form.notification_hour.data,
            notification_minute=form.notification_minute.data
        )
        db.session.add(policy)
        db.session.commit()
        flash('Policy has been added successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('add_policy.html', form=form, title="Add New Policy")

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_policy(id):
    policy = Policy.query.get_or_404(id)
    form = PolicyForm(obj=policy)
    if form.validate_on_submit():
        policy.name = form.name.data
        policy.due_date = form.due_date.data
        policy.details = form.details.data
        policy.email = form.email.data
        policy.notification_hour = form.notification_hour.data
        policy.notification_minute = form.notification_minute.data
        db.session.commit()
        flash('Policy has been updated!', 'success')
        return redirect(url_for('index'))
    return render_template('add_policy.html', form=form, title="Edit Policy")

@app.route('/delete/<int:id>')
def delete_policy(id):
    policy = Policy.query.get_or_404(id)
    db.session.delete(policy)
    db.session.commit()
    flash('Policy has been deleted!', 'success')
    return redirect(url_for('index'))

@app.route('/send_notification/<int:id>')
def send_notification_now(id):
    """Manually send a notification for a policy immediately."""
    policy = Policy.query.get_or_404(id)
    
    subject = f"Policy Reminder: {policy.name}"
    body = f"""
    <html>
      <body>
        <h2>Policy Reminder</h2>
        <p>This is a manual reminder about the following policy:</p>
        <p><strong>Policy Name:</strong> {policy.name}</p>
        <p><strong>Due Date:</strong> {policy.due_date.strftime('%Y-%m-%d')}</p>
        <p><strong>Details:</strong> {policy.details or 'No additional details provided.'}</p>
      </body>
    </html>
    """
    
    # Send email
    success = send_email(subject, body, policy.email)
    
    # Record the notification
    notification = Notification(
        policy_id=policy.id,
        subject=subject,
        recipient=policy.email,
        status='success' if success else 'failed'
    )
    db.session.add(notification)
    
    if success:
        policy.last_notified = datetime.now()
        db.session.commit()
        flash('Notification sent successfully!', 'success')
    else:
        db.session.commit()
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
    notifications = Notification.query.order_by(Notification.sent_at.desc()).paginate(page=page, per_page=20)
    return render_template('notifications.html', notifications=notifications, title="Notification History")

@app.route('/check_notifications')
def check_notifications():
    """API endpoint to check for new email notifications since the last check."""
    # Get the last time this was checked from session, default to 1 minute ago
    from datetime import timedelta
    last_check = session.get('last_notification_check', datetime.now() - timedelta(minutes=1))
    
    # Find notifications sent since the last check
    new_notifications = Notification.query.filter(
        Notification.sent_at > last_check,
        Notification.status == 'success'
    ).count()
    
    # Update the last check time
    session['last_notification_check'] = datetime.now()
    
    # Return JSON response
    return jsonify({
        'new_notifications': new_notifications > 0,
        'count': new_notifications
    })

if __name__ == '__main__':
    # Create database tables if they don't exist
    with app.app_context():
        db.create_all()
    
    # Start the scheduler
    scheduler.start()
    
    app.run(debug=True)
