# name file: database_modules/attendance_logger.py
import datetime
import os
import sys

# Add project root to sys.path to ensure modules are found
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database_modules.supabase_client import get_supabase_client
from utils.notifications import send_attendance_email 

def mark_attendance(employee_id):
    """
    Mark attendance + send email (using Supabase)
    """
    supabase = get_supabase_client()
    if not supabase:
        print("Error: Supabase client not initialized.")
        return False

    now = datetime.datetime.now()
    date_today = now.strftime("%Y-%m-%d")
    time_now = now.strftime("%H:%M:%S")

    try:
        # 1. Check for duplicates (Already marked today?)
        # Select * from attendance where employee_id = ? and date = ?
        response = supabase.table("attendance") \
            .select("*") \
            .eq("employee_id", employee_id) \
            .eq("date", date_today) \
            .execute()

        if response.data and len(response.data) > 0:
             return False # Already marked

        # 2. Mark Attendance
        # Logic to determine status based on time (Shift System)
        # Morning: 08:00 - 12:00
        # Afternoon: 13:00 - 16:30
        
        current_hour = now.hour
        current_minute = now.minute
        
        attendance_status = "Present" # Default
        
        if 5 <= current_hour < 12:
            attendance_status = "Morning Check-In"
        elif 12 <= current_hour < 13:
             attendance_status = "Morning Check-Out"
        elif 13 <= current_hour < 16:
             attendance_status = "Afternoon Check-In"
        elif 16 <= current_hour < 22:
             attendance_status = "Afternoon Check-Out"
        else:
             # Night / Other times
             attendance_status = "Check-In/Out"
        
        data = {
            "employee_id": employee_id,
            "date": date_today,
            "time": time_now,
            "status": attendance_status
        }
        
        insert_response = supabase.table("attendance").insert(data).execute()
        
        if insert_response.data:
            print(f"Success: Attendance marked for Employee ID: {employee_id} at {time_now}")
            
            # 3. Fetch Employee data for notification
            # We can do a join in Supabase, or just a simple fetch
            emp_response = supabase.table("employees").select("name, email").eq("id", employee_id).single().execute()
            
            if emp_response.data:
                employee_name = emp_response.data['name']
                email = emp_response.data['email']

                # Send Email in background
                print("Sending notification email...")
                send_attendance_email(email, employee_name, time_now, date_today, attendance_status)
            
            return True
        else:
            print("Error marking attendance: Insert failed.")
            return False

    except Exception as e:
        print(f"Error marking attendance: {e}")
        return False