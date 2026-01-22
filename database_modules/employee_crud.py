# name file : database_modules/employee_crud.py
import sqlite3
import pickle
import os

# Define database path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "attendance_system.db")

def get_db_connection():
    """Helper function to connect to the database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"❌ Connection error: {e}")
        return None

def add_new_employee(name, code, email, face_encoding, department="General"):
    """
    Function to add a new employee
    face_encoding: numpy array or list from face_recognition
    """
    conn = get_db_connection()
    if conn is None:
        return False

    try:
        # Convert face encoding to bytes
        encoding_blob = pickle.dumps(face_encoding)
        
        cursor = conn.cursor()
        sql = """
        INSERT INTO employees (name, employee_code, email, face_encoding, department)
        VALUES (?, ?, ?, ?, ?)
        """
        cursor.execute(sql, (name, code, email, encoding_blob, department))
        conn.commit()
        print(f"✅ Employee {name} has been added successfully!")
        return True
    except sqlite3.IntegrityError:
        print(f"⚠️ Error: The employee code {code} already exists!")
        return False
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        return False
    finally:
        conn.close()

def get_all_employees():
    """
    Function to retrieve all employees and their face encodings.
    Used for loading faces into system memory at startup.
    """
    conn = get_db_connection()
    employees_data = []
    
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, face_encoding FROM employees")
            rows = cursor.fetchall()
            
            for row in rows:
                try:
                    encoding = pickle.loads(row['face_encoding'])
                    employees_data.append({
                        "id": row['id'],
                        "name": row['name'],
                        "encoding": encoding
                    })
                except Exception as e:
                     print(f"❌ Error loading encoding for employee {row['id']}: {e}")

        except Exception as e:
            print(f"❌ Error during employee retrieval: {e}")
        finally:
            conn.close()
            
    return employees_data

def delete_employee_by_id(employee_id):
    """Delete an employee by ID"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM employees WHERE id = ?", (employee_id,))
            # Clean up attendance records for this employee
            cursor.execute("DELETE FROM attendance WHERE employee_id = ?", (employee_id,))
            
            conn.commit()
            print(f"🗑️ Deleted employee ID: {employee_id}")
            return True
        except Exception as e:
            print(f"❌ Error deleting employee: {e}")
            return False
        finally:
            conn.close()
    return False

def update_employee_data(employee_id, name, code, email, department="General"):
    """Update employee data (excluding face encoding)"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            sql = """
            UPDATE employees 
            SET name = ?, employee_code = ?, email = ?, department = ?
            WHERE id = ?
            """
            cursor.execute(sql, (name, code, email, department, employee_id))
            conn.commit()
            print(f"✏️ Updated employee ID: {employee_id}")
            return True
        except Exception as e:
            print(f"❌ Error updating employee: {e}")
            return False
        finally:
            conn.close()
    return False

def get_employee_by_id(employee_id):
    """Get a single employee's data by ID"""
    conn = get_db_connection()
    employee = None
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM employees WHERE id = ?", (employee_id,))
            employee = cursor.fetchone()
        finally:
            conn.close()
    return employee
