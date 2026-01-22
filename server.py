from waitress import serve
from web_interface.app import app
import os

if __name__ == "__main__":
    print("🚀 Starting Production Server for Smart Attendance...")
    print("🌍 Server running on http://localhost:8080")
    serve(app, host='localhost', port=8080)
