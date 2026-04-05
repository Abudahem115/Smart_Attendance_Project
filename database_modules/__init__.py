# database_modules package
from .supabase_client import get_supabase_client
from .employee_crud import (
    add_new_employee,
    get_all_employees,
    get_employee_by_id,
    update_employee_data,
    delete_employee_by_id,
)
from .attendance_logger import mark_attendance

__all__ = [
    "get_supabase_client",
    "add_new_employee",
    "get_all_employees",
    "get_employee_by_id",
    "update_employee_data",
    "delete_employee_by_id",
    "mark_attendance",
]
