"""
Email Notification Service
Sends email notifications for task completions
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from sqlalchemy.orm import Session
from .. import models


def send_task_completion_email(
    db: Session,
    user_id: int,
    task_type: str,
    task_id: int,
    status: str,
    brand_id: Optional[int] = None,
    error_message: Optional[str] = None
):
    """
    Send an email notification when a task completes or fails.

    Args:
        db: Database session
        user_id: User ID to send email to
        task_type: Type of task ('collection', 'analysis', 'report_generation')
        task_id: ID of the completed task
        status: Task status ('completed' or 'failed')
        brand_id: Optional brand ID
        error_message: Optional error message if task failed
    """
    # Get user email
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user or not user.email:
        print(f"No email found for user {user_id}")
        return

    # Get brand name if specified
    brand_name = "Your Brand"
    if brand_id:
        brand = db.query(models.BrandInfo).filter(models.BrandInfo.id == brand_id).first()
        if brand:
            brand_name = brand.brand_name

    # Map task types to friendly names
    task_type_names = {
        'collection': 'Data Collection',
        'analysis': 'Data Analysis',
        'report_generation': 'Report Generation'
    }
    task_name = task_type_names.get(task_type, task_type.title())

    # Create email subject and body based on status
    if status == 'completed':
        subject = f"TALES: {task_name} Complete - {brand_name}"
        logo_url = f"{os.getenv('FRONTEND_URL', 'https://tales.robotrachel.com')}/tales_logo.png"
        body = f"""
<html>
<body style="font-family: Arial, sans-serif; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background-color: #003e60; padding: 30px; text-align: center; border-radius: 8px 8px 0 0;">
            <img src="{logo_url}" alt="TALES" style="max-width: 200px; height: auto; margin-bottom: 20px;" />
            <h1 style="color: white; margin: 0;">Task Complete!</h1>
        </div>
        <div style="background-color: #f9f9f9; padding: 30px; border: 1px solid #e0e0e0; border-radius: 0 0 8px 8px;">
            <p style="font-size: 16px; line-height: 1.6;">
                Your <strong>{task_name}</strong> for <strong>{brand_name}</strong> has completed successfully.
            </p>
            <p style="font-size: 16px; line-height: 1.6;">
                Log in to TALES to view your results:
            </p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{os.getenv('FRONTEND_URL', 'http://localhost:5173')}"
                   style="background-color: #f04b25; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                    View Results
                </a>
            </div>
            <p style="font-size: 14px; color: #666; margin-top: 30px;">
                This is an automated notification from TALES. If you have questions, please contact admin@robotrachel.com.
            </p>
        </div>
    </div>
</body>
</html>
"""
    else:  # failed
        subject = f"TALES: {task_name} Failed - {brand_name}"
        error_details = error_message if error_message else "An unknown error occurred."
        logo_url = f"{os.getenv('FRONTEND_URL', 'https://tales.robotrachel.com')}/tales_logo.png"
        body = f"""
<html>
<body style="font-family: Arial, sans-serif; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background-color: #003e60; padding: 30px; text-align: center; border-radius: 8px 8px 0 0;">
            <img src="{logo_url}" alt="TALES" style="max-width: 200px; height: auto; margin-bottom: 20px;" />
            <h1 style="color: white; margin: 0;">Task Failed</h1>
        </div>
        <div style="background-color: #f9f9f9; padding: 30px; border: 1px solid #e0e0e0; border-radius: 0 0 8px 8px;">
            <p style="font-size: 16px; line-height: 1.6;">
                Your <strong>{task_name}</strong> for <strong>{brand_name}</strong> encountered an error and could not complete.
            </p>
            <div style="background-color: #fff; border-left: 4px solid #EA4A4A; padding: 15px; margin: 20px 0;">
                <p style="margin: 0; font-family: monospace; font-size: 14px;">
                    {error_details}
                </p>
            </div>
            <p style="font-size: 16px; line-height: 1.6;">
                Please try again or contact support if the problem persists.
            </p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{os.getenv('FRONTEND_URL', 'http://localhost:5173')}"
                   style="background-color: #f04b25; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                    Return to TALES
                </a>
            </div>
            <p style="font-size: 14px; color: #666; margin-top: 30px;">
                This is an automated notification from TALES. If you have questions, please contact admin@robotrachel.com.
            </p>
        </div>
    </div>
</body>
</html>
"""

    # Send email
    try:
        _send_email(user.email, subject, body)
        print(f"Task completion email sent to {user.email} for task {task_id}")
    except Exception as e:
        print(f"Failed to send task completion email: {e}")


def _send_email(to_email: str, subject: str, html_body: str):
    """
    Internal function to send an email via SMTP.

    Requires environment variables:
    - SMTP_HOST: SMTP server hostname
    - SMTP_PORT: SMTP server port
    - SMTP_USER: SMTP username
    - SMTP_PASSWORD: SMTP password
    - SMTP_FROM_EMAIL: From email address
    - SMTP_FROM_NAME: From name (optional)
    """
    smtp_host = os.getenv('SMTP_HOST')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    smtp_user = os.getenv('SMTP_USER')
    smtp_password = os.getenv('SMTP_PASSWORD')
    from_email = os.getenv('SMTP_FROM_EMAIL', smtp_user)
    from_name = os.getenv('SMTP_FROM_NAME', 'TALES')

    if not all([smtp_host, smtp_user, smtp_password]):
        print("SMTP configuration not set. Email not sent.")
        print(f"Would have sent email to {to_email} with subject: {subject}")
        return

    # Create message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = f"{from_name} <{from_email}>"
    msg['To'] = to_email

    # Add HTML body
    html_part = MIMEText(html_body, 'html')
    msg.attach(html_part)

    # Send email
    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
