# File: web_interface/app.py
"""
Smart Attendance System — Flask application factory.

All route logic has been extracted into Blueprints:
  - auth_bp       → login / logout / security
  - dashboard_bp  → main dashboard
  - employees_bp  → employee CRUD
  - attendance_bp → attendance list & CSV export
"""
import logging
import os
import sys

from flask import Flask, request
from flask_wtf.csrf import CSRFProtect

# Ensure project root is on the path for imports
_current_dir = os.path.dirname(os.path.abspath(__file__))
_project_dir = os.path.dirname(_current_dir)
if _project_dir not in sys.path:
    sys.path.insert(0, _project_dir)

from web_interface.config import Config
from web_interface.auth import auth_bp
from web_interface.routes import attendance_bp, dashboard_bp, employees_bp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def create_app() -> Flask:
    """Application factory."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # CSRF protection
    CSRFProtect(app)

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(employees_bp)
    app.register_blueprint(attendance_bp)

    # Security headers
    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if request.is_secure:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        return response

    logger.info("Flask application initialised with Blueprints.")
    return app


# Create a module-level app instance (used by run_web_server.py)
app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)