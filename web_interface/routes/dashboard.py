# File: web_interface/routes/dashboard.py
"""
Dashboard Blueprint — main landing page after login.
"""
import datetime
import logging
from collections import Counter

from flask import Blueprint, flash, render_template

from database_modules.supabase_client import get_supabase_client
from database_modules.employee_crud import get_all_employees
from web_interface.auth import login_required

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@login_required
def index():
    supabase = get_supabase_client()
    attendance_data = []
    today_count = 0
    total_employees = 0
    chart_dates = []
    chart_counts = []

    if supabase:
        try:
            today = datetime.datetime.now().strftime("%Y-%m-%d")

            # 1. Today's attendance
            att_response = (
                supabase.table("attendance")
                .select("*, employees(name, employee_code)")
                .eq("date", today)
                .order("time", desc=True)
                .execute()
            )

            raw_data = att_response.data
            for row in raw_data:
                emp = row.get("employees") or {}
                attendance_data.append(
                    {
                        "name": emp.get("name", "Unknown"),
                        "employee_code": emp.get("employee_code", "-"),
                        "date": row.get("date", "-"),
                        "time": row["time"],
                        "status": row["status"],
                    }
                )

            today_count = len(raw_data)

            # 2. Total employees
            all_employees = get_all_employees()
            total_employees = len(all_employees)

            # 3. Chart data — last 7 days
            seven_days_ago = (
                datetime.datetime.now() - datetime.timedelta(days=7)
            ).strftime("%Y-%m-%d")

            chart_response = (
                supabase.table("attendance")
                .select("date")
                .gte("date", seven_days_ago)
                .execute()
            )

            dates = [r["date"] for r in chart_response.data]
            date_counts = Counter(dates)
            sorted_dates = sorted(date_counts.keys())
            chart_dates = sorted_dates
            chart_counts = [date_counts[d] for d in sorted_dates]

        except Exception as e:
            logger.exception("Error loading dashboard: %s", e)
            flash("Error loading data. Please try again.", "warning")

    return render_template(
        "index.html",
        attendance=attendance_data,
        count=today_count,
        total_employees=total_employees,
        chart_dates=chart_dates,
        chart_counts=chart_counts,
    )
