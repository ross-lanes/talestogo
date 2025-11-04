"""
Help/Contact form endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
import logging

from ..database import get_db
from ..models import User
from ..auth import get_current_user
from ..email import send_email

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/help", tags=["help"])


class ContactRequest(BaseModel):
    subject: str
    message: str


@router.post("/contact")
async def send_contact_message(
    request: ContactRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a help/contact message to admin"""
    try:
        # Email content
        subject = f"TALES Support Request: {request.subject}"
        body = f"""Support request from TALES user:

From: {current_user.email}
User ID: {current_user.id}
Subject: {request.subject}

Message:
{request.message}

---
Sent via TALES Help & Support form
"""

        # Send email to admin
        admin_email = "admin@robotrachel.com"
        await send_email(admin_email, subject, body)

        logger.info(f"Help request sent from user {current_user.id} ({current_user.email})")

        return {
            "message": "Your message has been sent successfully. We'll get back to you soon!",
            "status": "success"
        }

    except Exception as e:
        logger.error(f"Failed to send help email: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to send message. Please try again or contact admin@robotrachel.com directly."
        )
