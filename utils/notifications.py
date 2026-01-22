# اسم الملف: utils/notifications.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- إعدادات البريد الإلكتروني ---
# استبدل هذه البيانات ببياناتك الحقيقية
SENDER_EMAIL = "aboodymaji@gmail.com"  # إيميلك الذي سيرسل الرسائل
SENDER_PASSWORD = "vusn mqqh qvrw pouv" # كلمة مرور التطبيقات (App Password) المكونة من 16 حرف

def send_attendance_email(to_email, student_name, time, date):
    """
    دالة لإرسال إيميل لولي الأمر
    """
    if not to_email or "@" not in to_email:
        print("⚠️ Warning: There is no valid email address for the parent.")
        return

    try:
        # إعداد محتوى الرسالة
        subject = f"🔔 Attendance Alert: {student_name}"
        body = f"""
        Dear Parent,
        
        This is an automated notification from the Smart Attendance System.
        
        ✅ Student Name: {student_name}
        🕒 Time: {time}
        📅 Date: {date}
        Status: Present
        
        Best Regards,
        School Administration
        """

        # تجهيز هيكل الإيميل
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # الاتصال بسيرفر Gmail
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls() # تفعيل التشفير
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        
        # إرسال الرسالة
        text = msg.as_string()
        server.sendmail(SENDER_EMAIL, to_email, text)
        server.quit()

        print(f"📧 Email sent successfully to {to_email}")
        return True

    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False