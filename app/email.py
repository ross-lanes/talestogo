"""
Email notification service

Supports two modes:
1. Resend API (recommended for Railway/cloud) - set RESEND_API_KEY
2. SMTP fallback - set SMTP_USER and SMTP_PASSWORD
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import logging
import httpx

logger = logging.getLogger(__name__)

# Resend API (recommended - works on Railway)
RESEND_API_KEY = os.getenv('RESEND_API_KEY')

# SMTP fallback (may not work on cloud platforms that block port 587)
SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
FROM_EMAIL = os.getenv('FROM_EMAIL', 'admin@robotrachel.com')


async def send_email(to_email: str, subject: str, body: str):
    """Send email notification via Resend API or SMTP fallback"""

    # Try Resend first (works on Railway)
    if RESEND_API_KEY:
        await _send_via_resend(to_email, subject, body)
        return

    # SMTP fallback
    if SMTP_USER and SMTP_PASSWORD:
        await _send_via_smtp(to_email, subject, body)
        return

    # No email service configured
    logger.info(f"Email not configured. Would send to {to_email}: {subject}")
    logger.info(f"Body: {body}")


async def _send_via_resend(to_email: str, subject: str, body: str):
    """Send email via Resend API (HTTP-based, works on Railway)"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {RESEND_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": FROM_EMAIL,
                    "to": [to_email],
                    "subject": subject,
                    "text": body,
                },
            )

            if response.status_code == 200:
                logger.info(f"Email sent via Resend to {to_email}")
            else:
                logger.error(f"Resend API error: {response.status_code} - {response.text}")
                raise Exception(f"Resend API error: {response.status_code}")

    except Exception as e:
        logger.error(f"Failed to send email via Resend: {str(e)}")
        raise


async def _send_via_smtp(to_email: str, subject: str, body: str):
    """Send email via SMTP (may not work on cloud platforms)"""
    msg = MIMEMultipart()
    msg['From'] = FROM_EMAIL
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        # Add timeout to prevent hanging
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        logger.info(f"Email sent via SMTP to {to_email}")
    except Exception as e:
        logger.error(f"Failed to send email via SMTP: {str(e)}")
        raise
