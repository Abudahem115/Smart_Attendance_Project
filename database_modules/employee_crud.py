# name file: database_modules/employee_crud.py
import json
import numpy as np
import face_recognition
from .supabase_client import get_supabase_client

def add_new_employee(name, code, email, face_encoding, department="General"):
    """
    Function to add a new employee with duplicate face check.
    face_encoding: numpy array or list from face_recognition
    """
    supabase = get_supabase_client()
    if not supabase:
        print("❌ Error: Supabase client not initialized.")
        return False

    try:
        # 1. Fetch all existing employees to check for duplicate faces
        # Note: For very large databases, this should be optimized (e.g., pgvector), 
        # but for now we fetch all and compare in Python as per request.
        
        print("🔍 Checking for duplicate faces...")
        all_employees = get_all_employees()
        
        if all_employees:
            existing_encodings = [e['encoding'] for e in all_employees]
            existing_names = [e['name'] for e in all_employees]
            
            # Compare the new face with all existing faces
            matches = face_recognition.compare_faces(existing_encodings, face_encoding, tolerance=0.5)
            
            if True in matches:
                first_match_index = matches.index(True)
                matched_name = existing_names[first_match_index]
                print(f"⚠️ Error: Possible duplicate detected! Face matches with existing employee: {matched_name}")
                return False

        # 2. Prepare data for insertion
        # Convert numpy array to list for JSON serialization
        if isinstance(face_encoding, np.ndarray):
            encoding_list = face_encoding.tolist()
        else:
            encoding_list = face_encoding

        data = {
            "name": name,
            "employee_code": code,
            "email": email,
            "department": department,
            "face_encoding": encoding_list # Store as JSON array
        }
        
        # 3. Insert into Supabase
        response = supabase.table("employees").insert(data).execute()
        
        # Supabase-py v2 returns an object with 'data'
        if response.data:
            print(f"✅ Employee {name} has been added successfully!")
            return True
        else:
             print("❌ Error adding employee: No data returned.")
             return False

    except Exception as e:
        print(f"❌ Error during add_employee: {e}")
        # Check for unique constraint violation on code/email if applicable
        if "duplicate key" in str(e):
             print(f"⚠️ Error: Employee code or Email likely already exists.")
        return False

def get_all_employees():
    """
    Function to retrieve all employees and their face encodings.
    Used for loading faces into system memory at startup and duplicate checking.
    """
    supabase = get_supabase_client()
    employees_data = []
    
    if not supabase:
         return employees_data

    try:
        # Fetch all columns including department and email for the list view
        response = supabase.table("employees").select("*").execute()
        
        rows = response.data
        
        for row in rows:
            try:
                # Supabase returns JSON automatically parsed as list/dict
                encoding_list = row['face_encoding']
                
                # Convert back to numpy array for face_recognition
                encoding_np = np.array(encoding_list)
                
                employees_data.append({
                    "id": row['id'],
                    "name": row['name'],
                    "employee_code": row.get('employee_code'),
                    "email": row.get('email'),
                    "department": row.get('department'),
                    "encoding": encoding_np
                })
            except Exception as e:
                    print(f"❌ Error parsing encoding for employee {row.get('name')}: {e}")

    except Exception as e:
        print(f"❌ Error retrieving employees: {e}")
            
    return employees_data

def delete_employee_by_id(employee_id):
    """Delete an employee by ID"""
    supabase = get_supabase_client()
    if not supabase:
        return False
        
    try:
        # Delete attendance records first (if no cascade delete setup)
        # supabase.table("attendance").delete().eq("employee_id", employee_id).execute()
        
        response = supabase.table("employees").delete().eq("id", employee_id).execute()
        
        if response.data:
            print(f"🗑️ Deleted employee ID: {employee_id}")
            return True
        else:
             print("❌ Error deleting employee or not found.")
             return False
             
    except Exception as e:
        print(f"❌ Error deleting employee: {e}")
        return False

def update_employee_data(employee_id, name, code, email, department="General"):
    """Update employee data (excluding face encoding)"""
    supabase = get_supabase_client()
    if not supabase:
        return False

    try:
        data = {
            "name": name,
            "employee_code": code,
            "email": email,
            "department": department
        }
        
        response = supabase.table("employees").update(data).eq("id", employee_id).execute()
        
        if response.data:
            print(f"✏️ Updated employee ID: {employee_id}")
            return True
        else:
             print("❌ Error updating employee.")
             return False

    except Exception as e:
        print(f"❌ Error updating employee: {e}")
        return False

def get_employee_by_id(employee_id):
    """Get a single employee's data by ID"""
    supabase = get_supabase_client()
    if not supabase:
        return None

    try:
        response = supabase.table("employees").select("*").eq("id", employee_id).single().execute()
        return response.data
    except Exception as e:
        print(f"❌ Error fetching employee: {e}")
        return None
