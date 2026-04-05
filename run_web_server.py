# File: run_web_server.py
"""
Production entry point for the Smart Attendance System.
Uses Waitress WSGI server for production-ready serving.
"""
import os

from waitress import serve
from web_interface.app import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8090))

    print("=" * 52)
    print("  Smart Attendance System  —  Production Server")
    print("=" * 52)
    print(f"  URL: http://localhost:{port}/login")
    print("=" * 52)

    serve(app, host="0.0.0.0", port=port)
