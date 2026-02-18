
import sys
import os

# Add project root to sys.path
import sys
import os

# Root directory usage
from waitress import serve
from web_interface.app import app

if __name__ == "__main__":
    # Get port from environment variable or use 8090 (Avoid 8000/8080)
    port = int(os.environ.get("PORT", 8090))
    
    print("Starting Production Server for Smart Attendance...")
    print(f"Server running on http://0.0.0.0:{port}")
    serve(app, host='0.0.0.0', port=port)
