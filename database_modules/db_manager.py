# name file : database_modules/db_manager.py
import sqlite3
import os

# the name of the database file
DB_NAME = "attendance_system.db"

# function to create a database connection
def create_connection():
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        print(f"✅ The database connection was successful: {DB_NAME}")
    except sqlite3.Error as e:
        print(f"❌ Database connection error: {e}")
    
    return conn

# function to create the necessary tables
def create_tables():
    # 1. SQL for Employees Table
    sql_create_employees_table = """
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        employee_code TEXT UNIQUE,
        email TEXT,
        face_encoding BLOB NOT NULL,
        department TEXT DEFAULT 'General',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

    # 2. SQL for Attendance Table
    sql_create_attendance_table = """
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        time TEXT NOT NULL,
        status TEXT DEFAULT 'Present',
        FOREIGN KEY (employee_id) REFERENCES employees (id)
    );
    """
    
    # 3. SQL for Admins Table (New)
    sql_create_admins_table = """
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL
    );
    """
    
    # --- التنفيذ (Execution) ---
    conn = create_connection()
    
    if conn is not None:
        try:
            cursor = conn.cursor()
            
            # تنفيذ إنشاء الجداول
            cursor.execute(sql_create_employees_table)
            cursor.execute(sql_create_attendance_table)
            cursor.execute(sql_create_admins_table) # إنشاء جدول الأدمن
            
            # إضافة أدمن افتراضي (Default Admin)
            try:
                cursor.execute("INSERT INTO admins (username, password) VALUES ('admin', '1234')")
                print("✅ Default Admin created: user=admin, pass=1234")
            except sqlite3.IntegrityError:
                pass # الأدمن موجود مسبقاً، لا داعي لإعادة إضافته
            
            conn.commit() # حفظ التغييرات
            print("✅ All tables (Employees, Attendance, Admins) created successfully.")
            
        except sqlite3.Error as e:
            print(f"❌ An error occurred while creating the tables: {e}")
        finally:
            conn.close() # إغلاق الاتصال
    else:
        print("❌ Error! A connection to the database could not be established.")

# تشغيل الملف مباشرة لتهيئة قاعدة البيانات
if __name__ == '__main__':
    # ضمان العمل في المجلد الرئيسي
    os.chdir(os.path.dirname(os.path.abspath(__file__))) 
    os.chdir('..') 
    
    create_tables()