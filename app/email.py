"""
Email notification service

Uses Resend API for sending emails (required for Railway deployment).
Requires RESEND_API_KEY and FROM_EMAIL environment variables.

For setup instructions, see CLAUDE.md
"""
import os
import logging
import httpx

logger = logging.getLogger(__name__)

# Resend API configuration (required)
RESEND_API_KEY = os.getenv('RESEND_API_KEY')
FROM_EMAIL = os.getenv('FROM_EMAIL', 'admin@robotrachel.com')


async def send_email(to_email: str, subject: str, body: str):
    """
    Send email notification via Resend API.

    Raises:
        ValueError: If RESEND_API_KEY is not configured
        Exception: If email send fails
    """
    if not RESEND_API_KEY:
        error_msg = "RESEND_API_KEY is not configured. Email sending is disabled."
        logger.error(error_msg)
        raise ValueError(error_msg)

    await _send_via_resend(to_email, subject, body)


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


