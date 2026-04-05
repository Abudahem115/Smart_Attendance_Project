# File: utils/notifications.py
"""
Email notification service for attendance alerts.
"""
import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Email settings from environment
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD", "")


def send_attendance_email(
    to_email: str,
    employee_name: str,
    time: str,
    date: str,
    status: str,
) -> bool:
    """
    Send an attendance notification email.

    Returns ``True`` on success, ``False`` on failure.
    """
    if not to_email or "@" not in to_email:
        logger.warning("Invalid email address: '%s' — skipping.", to_email)
        return False

    if not SENDER_EMAIL or not SENDER_PASSWORD:
        logger.warning("Sender email credentials not configured — skipping.")
        return False

    try:
        subject = f"Attendance Alert: {employee_name}"
        body = (
            f"Dear {employee_name},\n\n"
            f"This is an automated notification from the Smart Attendance System.\n\n"
            f"Employee Name: {employee_name}\n"
            f"Time: {time}\n"
            f"Date: {date}\n"
            f"Status: {status}\n\n"
            f"Best Regards,\n"
            f"HR Administration"
        )

        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        server.quit()

        logger.info("Email sent successfully to %s", to_email)
        return True

    except Exception as e:
        logger.exception("Failed to send email to %s: %s", to_email, e)
        return False