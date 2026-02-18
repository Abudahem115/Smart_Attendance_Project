
import sys
import os

# Add project root to sys.path
import sys
import os

# Root directory usage
from waitress import serve
from web_interface.app import app

if __name__ == "__main__":
    print("Starting Production Server for Smart Attendance...")
    print("Server running on http://localhost:8080")
    serve(app, host='localhost', port=8080)
