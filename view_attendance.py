# name file: view_attendance.py
from database_modules.supabase_client import get_supabase_client

# Connect to database
supabase = get_supabase_client()

print("\n--- 📋 HR Attendance Report (Today & Recent) ---")

if not supabase:
    print("❌ Error: Supabase connection failed.")
    exit()

try:
    # Fetch data joining attendance and employees
    # Note: Assuming 'employees' FK relationship exists on 'employee_id'
    response = supabase.table("attendance") \
        .select("time, status, employees(name, employee_code)") \
        .order("time", desc=True) \
        .limit(20) \
        .execute()
    
    rows = response.data

    if len(rows) == 0:
        print("No attendance records found yet.")
    else:
        print(f"{'Name':<20} | {'ID':<10} | {'Time':<10} | {'Status'}")
        print("-" * 55)
        for row in rows:
            emp = row.get('employees') or {}
            name = emp.get('name', 'Unknown')
            code = emp.get('employee_code', '-')
            
            # Truncate long names
            if len(name) > 19:
                name = name[:17] + ".."
                
            print(f"{name:<20} | {code:<10} | {row['time']:<10} | {row['status']}")

except Exception as e:
    print(f"❌ Error fetching records: {e}")

input("\nPress Enter to exit...")