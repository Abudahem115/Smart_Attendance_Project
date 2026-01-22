# name file: database_modules/attendance_logger.py
import sqlite3
import datetime
import os
import sys

# Add path to import notifications
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.notifications import send_attendance_email 

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "attendance_system.db")

def mark_attendance(employee_id):
    """
    Mark attendance + send email
    """
    now = datetime.datetime.now()
    date_today = now.strftime("%Y-%m-%d")
    time_now = now.strftime("%H:%M:%S")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row # Important for accessing columns by name
    cursor = conn.cursor()

    try:
        # 1. Check for duplicates
        check_sql = "SELECT * FROM attendance WHERE employee_id = ? AND date = ?"
        cursor.execute(check_sql, (employee_id, date_today))
        existing_record = cursor.fetchone()

        if existing_record:
            return False # Already marked
        
        # 2. Mark Attendance
        insert_sql = "INSERT INTO attendance (employee_id, date, time, status) VALUES (?, ?, ?, 'Present')"
        cursor.execute(insert_sql, (employee_id, date_today, time_now))
        conn.commit()
        
        print(f"✅ Success: Attendance marked for Employee ID: {employee_id} at {time_now}")

        # 3. Fetch Employee data (Name and Email) for notification
        employee_sql = "SELECT name, email FROM employees WHERE id = ?"
        cursor.execute(employee_sql, (employee_id,))
        employee_data = cursor.fetchone()

        if employee_data:
            employee_name = employee_data['name']
            email = employee_data['email']
            
            # 🔥 Send Email in background
            print("⏳ Sending notification email...")
            send_attendance_email(email, employee_name, time_now, date_today)

        return True

    except Exception as e:
        print(f"❌ Error marking attendance: {e}")
        return False
    finally:
        conn.close()