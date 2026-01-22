# اسم الملف: view_attendance.py
import sqlite3

# Connect to database
conn = sqlite3.connect("attendance_system.db")
cursor = conn.cursor()

print("\n--- 📋 HR Attendance Report (Today) ---")

# Fetch data joining attendance and employees
sql = """
SELECT employees.name, employees.employee_code, attendance.time, attendance.status
FROM attendance
JOIN employees ON attendance.employee_id = employees.id
ORDER BY attendance.time DESC
"""

cursor.execute(sql)
rows = cursor.fetchall()

if len(rows) == 0:
    print("No attendance records found yet.")
else:
    print(f"{'Name':<20} | {'ID':<10} | {'Time':<10} | {'Status'}")
    print("-" * 55)
    for row in rows:
        print(f"{row[0]:<20} | {row[1]:<10} | {row[2]:<10} | {row[3]}")

conn.close()
input("\nPress Enter to exit...")