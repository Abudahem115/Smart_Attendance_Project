# File: web_interface/routes/attendance.py
"""
Attendance Blueprint — list, filter by month, CSV export.
"""
import calendar
import csv
import datetime
import logging
from io import StringIO

from flask import (
    Blueprint,
    flash,
    make_response,
    render_template,
    request,
)

from database_modules.employee_crud import get_all_employees
from database_modules.supabase_client import get_supabase_client
from web_interface.auth import login_required

logger = logging.getLogger(__name__)

attendance_bp = Blueprint("attendance", __name__)


def _get_month_range(year: int, month: int):
    """Return (start_date, end_date) strings for a given year/month."""
    _, last_day = calendar.monthrange(year, month)
    start_date = f"{year}-{month:02d}-01"
    end_date = f"{year}-{month:02d}-{last_day:02d}"
    return start_date, end_date


@attendance_bp.route("/attendance")
@login_required
def attendance_list():
    supabase = get_supabase_client()
    attendance_data = []

    now = datetime.datetime.now()
    try:
        selected_month = int(request.args.get("month", str(now.month)))
    except ValueError:
        selected_month = now.month

    start_date, end_date = _get_month_range(now.year, selected_month)

    if supabase:
        try:
            response = (
                supabase.table("attendance")
                .select("*, employees(name, employee_code, department)")
                .gte("date", start_date)
                .lte("date", end_date)
                .order("date", desc=True)
                .order("time", desc=True)
                .execute()
            )

            for row in response.data:
                emp = row.get("employees") or {}
                attendance_data.append(
                    {
                        "name": emp.get("name", "Unknown"),
                        "employee_code": emp.get("employee_code", "-"),
                        "department": emp.get("department", "-"),
                        "date": row.get("date", "-"),
                        "time": row["time"],
                        "status": row["status"],
                    }
                )
        except Exception as e:
            logger.exception("Error loading attendance list: %s", e)
            flash("Error loading attendance data.", "warning")

    # Summary stats
    attended_ids = {row["employee_code"] for row in attendance_data}
    all_employees = get_all_employees()
    total_employees = len(all_employees)
    total_attended = len(attended_ids)
    total_not_attended = total_employees - total_attended

    return render_template(
        "attendance_list.html",
        attendance_data=attendance_data,
        total_records=len(attendance_data),
        total_attended=total_attended,
        total_not_attended=total_not_attended,
        selected_month=selected_month,
    )


@attendance_bp.route("/export_attendance")
@login_required
def export_attendance():
    supabase = get_supabase_client()
    rows = []

    now = datetime.datetime.now()
    try:
        selected_month = int(request.args.get("month", str(now.month)))
    except ValueError:
        selected_month = now.month

    start_date, end_date = _get_month_range(now.year, selected_month)

    if supabase:
        try:
            response = (
                supabase.table("attendance")
                .select("*, employees(name, employee_code)")
                .gte("date", start_date)
                .lte("date", end_date)
                .order("date", desc=True)
                .order("time", desc=True)
                .execute()
            )
            rows = response.data
        except Exception as e:
            logger.exception("Error fetching export data: %s", e)
            flash(f"Error fetching export data.", "danger")

    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(["Employee Name", "ID Code", "Date", "Time", "Status"])

    for row in rows:
        emp = row.get("employees") or {}
        cw.writerow(
            [
                emp.get("name", "Unknown"),
                emp.get("employee_code", "-"),
                row["date"],
                row["time"],
                row["status"],
            ]
        )

    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=attendance_report.csv"
    output.headers["Content-type"] = "text/csv"
    return output
