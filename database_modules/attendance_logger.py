# File: database_modules/attendance_logger.py
"""
Mark attendance and send email notifications through Supabase.
"""
import datetime
import logging

from .supabase_client import get_supabase_client
from utils.attendance_status import determine_attendance_status
from utils.notifications import send_attendance_email

logger = logging.getLogger(__name__)


def mark_attendance(employee_id: int) -> bool:
    """
    Mark attendance for *employee_id* and send an email notification.

    Returns ``True`` on success, ``False`` if already marked or on error.
    """
    supabase = get_supabase_client()
    if not supabase:
        logger.error("Supabase client not initialised.")
        return False

    now = datetime.datetime.now()
    date_today = now.strftime("%Y-%m-%d")
    time_now = now.strftime("%H:%M:%S")

    try:
        # 1. Duplicate check — already marked today?
        response = (
            supabase.table("attendance")
            .select("*")
            .eq("employee_id", employee_id)
            .eq("date", date_today)
            .execute()
        )

        if response.data and len(response.data) > 0:
            logger.info("Attendance already marked for employee %s today.", employee_id)
            return False

        # 2. Determine status using shared utility
        attendance_status = determine_attendance_status(now.hour)

        data = {
            "employee_id": employee_id,
            "date": date_today,
            "time": time_now,
            "status": attendance_status,
        }

        insert_response = supabase.table("attendance").insert(data).execute()

        if insert_response.data:
            logger.info(
                "Attendance marked for employee %s at %s — %s",
                employee_id,
                time_now,
                attendance_status,
            )

            # 3. Fetch employee data for notification
            emp_response = (
                supabase.table("employees")
                .select("name, email")
                .eq("id", employee_id)
                .single()
                .execute()
            )

            if emp_response.data:
                employee_name = emp_response.data["name"]
                email = emp_response.data["email"]
                logger.info("Sending notification email to %s …", email)
                send_attendance_email(
                    email, employee_name, time_now, date_today, attendance_status
                )

            return True

        logger.error("Attendance insert failed for employee %s.", employee_id)
        return False

    except Exception as e:
        logger.exception("Error marking attendance for employee %s: %s", employee_id, e)
        return False