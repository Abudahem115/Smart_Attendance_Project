# File: utils/notifications.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


import os
from dotenv import load_dotenv

load_dotenv()

# --- Email Settings ---
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")

def send_attendance_email(to_email, employee_name, time, date, status):
    """
    Function to send email notification to the employee
    """
    if not to_email or "@" not in to_email:
        print("Warning: Invalid email address.")
        return

    try:
        # Prepare content
        subject = f"Attendance Alert: {employee_name}"
        body = f"""
        Dear {employee_name},
        
        This is an automated notification from the Smart Attendance System.
        
        Employee Name: {employee_name}
        Time: {time}
        Date: {date}
        Status: {status}
        
        Best Regards,
        HR Administration
        """

        # Prepare structure
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Connect to Gmail Server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls() # Enable encryption
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        
        # Send
        text = msg.as_string()
        server.sendmail(SENDER_EMAIL, to_email, text)
        server.quit()

        print(f"Email sent successfully to {to_email}")
        return True

    except Exception as e:
        print(f"Failed to send email: {e}")
        return False