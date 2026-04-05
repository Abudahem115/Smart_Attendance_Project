# File: database_modules/employee_crud.py
"""
CRUD operations for the employees table in Supabase.
"""
import logging
from typing import Any, Dict, List, Optional, Union

import face_recognition
import numpy as np

from .supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


def add_new_employee(
    name: str,
    code: str,
    email: str,
    face_encoding: Union[np.ndarray, list],
    department: str = "General",
) -> bool:
    """
    Add a new employee with duplicate-face checking.

    Args:
        name: Employee full name.
        code: Unique employee code.
        email: Employee email address.
        face_encoding: 128-d face encoding (numpy array or list).
        department: Department name.

    Returns:
        ``True`` on success, ``False`` if duplicate or error.
    """
    supabase = get_supabase_client()
    if not supabase:
        logger.error("Supabase client not initialised.")
        return False

    try:
        # 1. Check for duplicate faces
        logger.info("Checking for duplicate faces …")
        all_employees = get_all_employees()

        if all_employees:
            existing_encodings = [e["encoding"] for e in all_employees]
            existing_names = [e["name"] for e in all_employees]

            matches = face_recognition.compare_faces(
                existing_encodings, face_encoding, tolerance=0.5
            )

            if True in matches:
                first_match_index = matches.index(True)
                matched_name = existing_names[first_match_index]
                logger.warning(
                    "Duplicate detected — face matches existing employee: %s",
                    matched_name,
                )
                return False

        # 2. Prepare data
        encoding_list = (
            face_encoding.tolist()
            if isinstance(face_encoding, np.ndarray)
            else face_encoding
        )

        data = {
            "name": name,
            "employee_code": code,
            "email": email,
            "department": department,
            "face_encoding": encoding_list,
        }

        # 3. Insert into Supabase
        response = supabase.table("employees").insert(data).execute()

        if response.data:
            logger.info("Employee '%s' added successfully.", name)
            return True

        logger.error("Insert returned no data for employee '%s'.", name)
        return False

    except Exception as e:
        logger.exception("Error adding employee '%s': %s", name, e)
        if "duplicate key" in str(e):
            logger.warning("Employee code or email likely already exists.")
        return False


def get_all_employees() -> List[Dict[str, Any]]:
    """Retrieve all employees with their face encodings parsed as numpy arrays."""
    supabase = get_supabase_client()
    if not supabase:
        return []

    employees_data: List[Dict[str, Any]] = []

    try:
        response = supabase.table("employees").select("*").execute()

        for row in response.data:
            try:
                encoding_np = np.array(row["face_encoding"])
                employees_data.append(
                    {
                        "id": row["id"],
                        "name": row["name"],
                        "employee_code": row.get("employee_code"),
                        "email": row.get("email"),
                        "department": row.get("department"),
                        "encoding": encoding_np,
                    }
                )
            except Exception as e:
                logger.error(
                    "Error parsing encoding for employee '%s': %s",
                    row.get("name"),
                    e,
                )
    except Exception as e:
        logger.exception("Error retrieving employees: %s", e)

    return employees_data


def delete_employee_by_id(employee_id: int) -> bool:
    """Delete an employee by their database ID."""
    supabase = get_supabase_client()
    if not supabase:
        return False

    try:
        response = (
            supabase.table("employees").delete().eq("id", employee_id).execute()
        )
        if response.data:
            logger.info("Deleted employee ID: %s", employee_id)
            return True

        logger.error("Delete returned no data for employee ID %s.", employee_id)
        return False
    except Exception as e:
        logger.exception("Error deleting employee ID %s: %s", employee_id, e)
        return False


def update_employee_data(
    employee_id: int,
    name: str,
    code: str,
    email: str,
    department: str = "General",
) -> bool:
    """Update employee metadata (face encoding is not changed)."""
    supabase = get_supabase_client()
    if not supabase:
        return False

    try:
        data = {
            "name": name,
            "employee_code": code,
            "email": email,
            "department": department,
        }

        response = (
            supabase.table("employees")
            .update(data)
            .eq("id", employee_id)
            .execute()
        )

        if response.data:
            logger.info("Updated employee ID: %s", employee_id)
            return True

        logger.error("Update returned no data for employee ID %s.", employee_id)
        return False
    except Exception as e:
        logger.exception("Error updating employee ID %s: %s", employee_id, e)
        return False


def get_employee_by_id(employee_id: int) -> Optional[Dict[str, Any]]:
    """Fetch a single employee record by ID."""
    supabase = get_supabase_client()
    if not supabase:
        return None

    try:
        response = (
            supabase.table("employees")
            .select("*")
            .eq("id", employee_id)
            .single()
            .execute()
        )
        return response.data
    except Exception as e:
        logger.exception("Error fetching employee ID %s: %s", employee_id, e)
        return None
