# File: web_interface/routes/employees.py
"""
Employee management Blueprint — list, add, edit, delete.
"""
import logging
import uuid

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from database_modules.employee_crud import (
    add_new_employee,
    delete_employee_by_id,
    get_all_employees,
    get_employee_by_id,
    update_employee_data,
)
from web_interface.auth import login_required
from web_interface.services.face_service import (
    compute_average_encoding,
    process_captured_photos,
    process_uploaded_photos,
)

logger = logging.getLogger(__name__)

employees_bp = Blueprint("employees", __name__)


@employees_bp.route("/employees")
@login_required
def employees_list():
    employees = get_all_employees()
    return render_template("employees.html", employees=employees)


@employees_bp.route("/add_employee", methods=["GET", "POST"])
@login_required
def add_employee():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        department = request.form.get("department", "General").strip()

        # Auto-generate employee code
        code = f"EMP{uuid.uuid4().hex[:8].upper()}"

        if not name or not email:
            flash("Name and Email are required.", "warning")
            return render_template("add_employee.html")

        upload_folder = current_app.config["UPLOAD_FOLDER"]
        all_encodings = []

        # 1. Process uploaded photos
        files = request.files.getlist("photos")
        all_encodings.extend(process_uploaded_photos(files, upload_folder))

        # 2. Process captured photos
        captured_list = request.form.getlist("captured_photos")
        if captured_list:
            all_encodings.extend(
                process_captured_photos(captured_list, upload_folder, code)
            )

        # 3. Save
        avg_encoding = compute_average_encoding(all_encodings)

        if avg_encoding is not None:
            success = add_new_employee(name, code, email, avg_encoding, department)
            if success:
                flash(f"Successfully added {name} (ID: {code}).", "success")
                return redirect(url_for("employees.employees_list"))
            else:
                flash(
                    "Error: Employee face may already be registered.",
                    "danger",
                )
        else:
            flash(
                "No face detected. Please ensure face is clearly visible.",
                "warning",
            )

    return render_template("add_employee.html")


@employees_bp.route("/edit_employee/<int:id>", methods=["GET", "POST"])
@login_required
def edit_employee(id):
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        code = request.form.get("code", "").strip()
        email = request.form.get("email", "").strip()
        department = request.form.get("department", "General").strip()

        if not name or not code or not email:
            flash("All fields are required.", "warning")
            employee = get_employee_by_id(id)
            return render_template("edit_employee.html", employee=employee)

        success = update_employee_data(id, name, code, email, department)
        if success:
            flash("Employee details updated successfully.", "success")
            return redirect(url_for("employees.employees_list"))
        else:
            flash("Error updating employee.", "danger")

    employee = get_employee_by_id(id)
    return render_template("edit_employee.html", employee=employee)


@employees_bp.route("/delete_employee/<int:id>", methods=["POST"])
@login_required
def delete_employee(id):
    success = delete_employee_by_id(id)
    if success:
        flash("Employee deleted successfully.", "success")
    else:
        flash("Error deleting employee.", "danger")
    return redirect(url_for("employees.employees_list"))
