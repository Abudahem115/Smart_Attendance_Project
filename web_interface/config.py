# File: web_interface/config.py
"""
Centralised application configuration for the Flask web interface.
"""
import datetime
import os

# Directory paths
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(CURRENT_DIR)

# Upload folders
UPLOAD_FOLDER = os.path.join(CURRENT_DIR, "static", "uploads")
PROCESSED_FOLDER = os.path.join(CURRENT_DIR, "static", "processed")

# Ensure folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

# Department list (shared between add & edit forms)
DEPARTMENTS = [
    "General",
    "Administration",
    "Human Resources",
    "Information Technology",
    "Finance",
    "Marketing",
    "Sales",
    "Operations",
    "Engineering",
    "Security",
    "Maintenance",
]


class Config:
    """Flask application configuration."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev_fallback_key")
    PERMANENT_SESSION_LIFETIME = datetime.timedelta(minutes=30)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    UPLOAD_FOLDER = UPLOAD_FOLDER
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB upload limit
