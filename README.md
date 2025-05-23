# Policy Notifier

A web application that helps you keep track of important policy deadlines and sends email reminders using SMTP.

## Features

- Add, edit, and delete policy notifications
- Automatic email reminders when policies are due
- Configurable SMTP settings for email delivery
- User-friendly interface with visual indicators for upcoming deadlines
- Customizable notification times for each policy

## Setup Instructions

### 1. Clone the repository

```bash
git clone <repository-url>
cd policy_notifier
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the virtual environment

#### On Windows:
```bash
venv\Scripts\activate
```

#### On macOS/Linux:
```bash
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure SMTP Settings

Create a `.env` file in the root directory by copying the template:

```bash
cp .env.template .env
```

Edit the `.env` file with your actual SMTP settings:

```
SECRET_KEY=your-secret-key-here
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password-here
EMAIL_SENDER=your-email@gmail.com
EMAIL_RECIPIENT=default-recipient@example.com
```

### Gmail SMTP Setup Instructions:

1. Enable 2-Step Verification in your Google Account
2. Generate an App Password:
   - Go to your Google Account > Security
   - Under "Signing in to Google," select App Passwords
   - Select "Mail" and your device type
   - Click Generate
   - Copy the 16-character password
3. Use this App Password as your `SMTP_PASSWORD` in the .env file

### 6. Run the application

```bash
python app.py
```

The application will be available at `http://localhost:5000`.

## Usage

1. **Add a policy**: Click on "Add New Policy" and fill out the form with policy details.
2. **Edit a policy**: Click on the pencil icon on any policy card to edit its details.
3. **Delete a policy**: Click on the trash icon on any policy card to delete it.
4. **Test email configuration**: Click on "SMTP Configuration" at the bottom of the page to test your email setup.

## Email Notifications

The system automatically checks for policies due each day at 9:00 AM and sends email notifications for those policies. You can customize this schedule by modifying the `scheduler.add_job()` configuration in `app.py`.

## Free Hosting Options

### Option 1: Render

[Render](https://render.com/) offers a free tier for web services:

1. Create an account on Render
2. Create a new Web Service
3. Connect your GitHub repository
4. Configure the build settings:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app_sqlite:app`
5. Add your environment variables in the Render dashboard (same as in your .env file)

### Option 2: PythonAnywhere

[PythonAnywhere](https://www.pythonanywhere.com/) offers a free tier for Flask applications:

1. Create an account on PythonAnywhere
2. Go to the Web tab and create a new web app
3. Select Flask and the appropriate Python version
4. Set up your WSGI file to point to your application
5. Upload your files via the Files tab or git clone your repository
6. Set up the environment variables in the WSGI configuration file

### Option 3: Railway

[Railway](https://railway.app/) offers a free starter plan:

1. Create an account on Railway
2. Connect your GitHub repository
3. Create a new project from your repository
4. Add the environment variables
5. Deploy the application

## Pre-deployment Checklist

1. Update `requirements.txt` to include gunicorn:
```bash
pip install gunicorn
pip freeze > requirements.txt
```

2. Configure the app for production by modifying the bottom of app_sqlite.py:
```python
if __name__ == '__main__':
    # Initialize the database
    init_db()
    
    # Start the scheduler
    scheduler.start()
    
    # Get port from environment variable or use 5000 as default
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
```

3. Make sure your `.env` file is not committed to version control (add it to `.gitignore`)

## License

MIT
#   P O L I C Y _ N O T I F I E R 
 
 