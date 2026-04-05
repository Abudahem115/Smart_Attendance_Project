# File: web_interface/routes/__init__.py
"""
Route Blueprints registry.
"""
from .attendance import attendance_bp
from .dashboard import dashboard_bp
from .employees import employees_bp

__all__ = ["dashboard_bp", "employees_bp", "attendance_bp"]
