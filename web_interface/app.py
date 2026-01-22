# اسم الملف: web_interface/app.py
from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response
import sqlite3
import os
import sys
import face_recognition
import numpy as np
import base64
import cv2
import csv
from io import StringIO
from functools import wraps
import datetime

# إعداد المسارات
current_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(current_dir)
sys.path.append(project_dir)

# Import Employee CRUD
from database_modules.employee_crud import (
    add_new_employee, 
    delete_employee_by_id, 
    get_employee_by_id, 
    update_employee_data,
    get_all_employees
)
from database_modules.attendance_logger import mark_attendance

# إعداد التطبيق
app = Flask(__name__)
app.secret_key = "super_secret_key" # مفتاح لتشفير الجلسة (Session)

# إعداد المجلدات
UPLOAD_FOLDER = os.path.join(current_dir, 'static', 'uploads')
PROCESSED_FOLDER = os.path.join(current_dir, 'static', 'processed')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

DB_PATH = os.path.join(project_dir, "attendance_system.db")

# --- Helper Functions ---

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# --- Security Decorator (نظام الحماية) ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            flash('Please login to access the system.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Authentication Routes (تسجيل الدخول والخروج) ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        try:
            admin = conn.execute('SELECT * FROM admins WHERE username = ? AND password = ?', (username, password)).fetchone()
            
            if admin:
                session['admin_logged_in'] = True
                session['username'] = username
                flash('✅ Welcome back, Admin!', 'success')
                return redirect(url_for('index'))
            else:
                flash('❌ Invalid Username or Password', 'danger')
        except Exception as e:
            flash(f'Error: {e}', 'danger')
        finally:
            conn.close()
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('ℹ️ You have been logged out.', 'info')
    return redirect(url_for('login'))

# --- Main Routes (الصفحات الرئيسية) ---

@app.route('/')
@login_required
def index():
    conn = get_db_connection()
    
    # 1. Last 10 attendance records
    attendance_sql = """
    SELECT employees.name, employees.employee_code, attendance.time, attendance.status
    FROM attendance
    JOIN employees ON attendance.employee_id = employees.id
    ORDER BY attendance.id DESC LIMIT 10
    """
    attendance_data = conn.execute(attendance_sql).fetchall()
    
    # 2. عدد الحضور اليوم
    count_sql = "SELECT count(*) FROM attendance WHERE date = date('now')"
    today_count = conn.execute(count_sql).fetchone()[0]
    
    # 3. بيانات الرسم البياني (آخر 7 أيام)
    chart_sql = """
    SELECT date, COUNT(*) as count 
    FROM attendance 
    GROUP BY date 
    ORDER BY date DESC 
    LIMIT 7
    """
    chart_data = conn.execute(chart_sql).fetchall()
    
    # تنسيق البيانات للرسم البياني
    chart_dates = [row['date'] for row in reversed(chart_data)]
    chart_counts = [row['count'] for row in reversed(chart_data)]
    
    conn.close()
    
    return render_template('index.html', 
                           attendance=attendance_data, 
                           count=today_count,
                           chart_dates=chart_dates,
                           chart_counts=chart_counts)

@app.route('/employees')
@login_required
def employees_list():
    conn = get_db_connection()
    employees = conn.execute('SELECT * FROM employees').fetchall()
    conn.close()
    return render_template('employees.html', employees=employees)

# --- Employee Management Routes ---

@app.route('/add_employee', methods=['GET', 'POST'])
@login_required
def add_employee():
    if request.method == 'POST':
        name = request.form['name']
        code = request.form['code']
        email = request.form['email']
        department = request.form.get('department', 'General')
        
        all_encodings = []
        
        # 1. Process Uploaded Photos
        files = request.files.getlist('photos')
        for file in files:
            if file and file.filename != '':
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                file.save(filepath)
                try:
                    img = face_recognition.load_image_file(filepath)
                    encs = face_recognition.face_encodings(img)
                    if len(encs) > 0:
                        all_encodings.append(encs[0])
                    os.remove(filepath)
                except:
                    pass

        # 2. Process Captured Photos
        captured_list = request.form.getlist('captured_photos') 
        if captured_list:
            for i, item in enumerate(captured_list):
                try:
                    if "," in item:
                        header, encoded = item.split(",", 1)
                        data = base64.b64decode(encoded)
                        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], f"capture_{code}_{i}.jpg")
                        with open(temp_path, "wb") as f:
                            f.write(data)
                        
                        img = face_recognition.load_image_file(temp_path)
                        encs = face_recognition.face_encodings(img)
                        if len(encs) > 0:
                            all_encodings.append(encs[0])
                        os.remove(temp_path)
                except Exception as e:
                    print(f"❌ Error in image {i}: {e}")

        # Save to DB
        if len(all_encodings) > 0:
            avg_encoding = np.mean(all_encodings, axis=0)
            success = add_new_employee(name, code, email, avg_encoding, department)
            
            if success:
                flash(f'✅ Successfully added {name} (Trained with {len(all_encodings)} images).', 'success')
                return redirect(url_for('employees_list'))
            else:
                flash('❌ Error: Employee ID might already exist.', 'danger')
        else:
            flash('⚠️ No face detected! Please ensure face is visible.', 'warning')

    return render_template('add_employee.html')

@app.route('/edit_employee/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_employee(id):
    if request.method == 'POST':
        name = request.form['name']
        code = request.form['code']
        email = request.form['email']
        department = request.form.get('department', 'General')
        
        success = update_employee_data(id, name, code, email, department)
        if success:
            flash('✅ Employee details updated successfully!', 'success')
            return redirect(url_for('employees_list'))
        else:
            flash('❌ Error updating employee.', 'danger')
    
    employee = get_employee_by_id(id)
    return render_template('edit_employee.html', employee=employee)

@app.route('/delete_employee/<int:id>')
@login_required
def delete_employee(id):
    success = delete_employee_by_id(id)
    if success:
        flash('🗑️ Employee deleted successfully.', 'success')
    else:
        flash('❌ Error deleting employee.', 'danger')
    return redirect(url_for('employees_list'))

# --- Advanced Features (التحضير الجماعي والتقارير) ---

@app.route('/hr_scan', methods=['GET', 'POST'])
@login_required
def hr_scan():
    processed_image_name = None
    present_names = []
    present_count = 0

    if request.method == 'POST':
        file = request.files['group_photo']
        if file:
            filename = "class_temp.jpg"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Process Image
            image = face_recognition.load_image_file(filepath)
            face_locations = face_recognition.face_locations(image)
            face_encodings = face_recognition.face_encodings(image, face_locations)

            # Get data for comparison
            all_employees = get_all_employees()
            known_encodings = [s['encoding'] for s in all_employees]
            known_names = [s['name'] for s in all_employees]
            known_ids = [s['id'] for s in all_employees]

            # Prepare OpenCV
            opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=0.5)
                name = "Unknown"
                color = (0, 0, 255)

                face_distances = face_recognition.face_distance(known_encodings, face_encoding)
                if len(face_distances) > 0:
                    best_match_index = np.argmin(face_distances)
                    if matches[best_match_index]:
                        name = known_names[best_match_index]
                        student_id = known_ids[best_match_index]
                        color = (0, 255, 0)
                        
                        if mark_attendance(student_id):
                            print(f"✅ Marked present via Group Scan: {name}")
                        present_names.append(name)

                cv2.rectangle(opencv_image, (left, top), (right, bottom), color, 2)
                cv2.putText(opencv_image, name, (left, bottom + 20), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)

            # Save Result
            result_filename = f"result_{datetime.datetime.now().strftime('%H%M%S')}.jpg"
            result_path = os.path.join(PROCESSED_FOLDER, result_filename)
            cv2.imwrite(result_path, opencv_image)
            
            processed_image_name = result_filename
            present_count = len(present_names)
            os.remove(filepath)

    return render_template('scan_result.html', 
                           processed_image=processed_image_name, 
                           present_names=present_names,
                           present_count=present_count)

@app.route('/export_attendance')
@login_required
def export_attendance():
    conn = get_db_connection()
    sql = """
    SELECT employees.name, employees.employee_code, attendance.date, attendance.time, attendance.status
    FROM attendance
    JOIN employees ON attendance.employee_id = employees.id
    ORDER BY attendance.date DESC, attendance.time DESC
    """
    rows = conn.execute(sql).fetchall()
    conn.close()

    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['Employee Name', 'ID Code', 'Date', 'Time', 'Status'])
    for row in rows:
        cw.writerow([row['name'], row['employee_code'], row['date'], row['time'], row['status']])

    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=attendance_report.csv"
    output.headers["Content-type"] = "text/csv"
    return output

if __name__ == '__main__':
    app.run(debug=True, port=5000)