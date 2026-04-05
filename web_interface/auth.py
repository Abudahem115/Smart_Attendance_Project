# File: web_interface/auth.py
"""
Authentication Blueprint — login, logout, security decorators, rate limiting.
"""
import logging
import time
from functools import wraps

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash

from database_modules.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__)

# ── In-memory rate limiting ──────────────────────────────────
_login_attempts: dict = {}
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION = 300  # seconds


def _is_rate_limited(ip: str) -> bool:
    if ip in _login_attempts:
        attempts, last_attempt = _login_attempts[ip]
        if attempts >= MAX_LOGIN_ATTEMPTS:
            if time.time() - last_attempt < LOCKOUT_DURATION:
                return True
            del _login_attempts[ip]
    return False


def _record_failed_login(ip: str) -> None:
    if ip in _login_attempts:
        attempts, _ = _login_attempts[ip]
        _login_attempts[ip] = (attempts + 1, time.time())
    else:
        _login_attempts[ip] = (1, time.time())


def _clear_login_attempts(ip: str) -> None:
    _login_attempts.pop(ip, None)


# ── Decorator ────────────────────────────────────────────────
def login_required(f):
    """Redirect unauthenticated users to the login page."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "admin_logged_in" not in session:
            flash("Please login to access the system.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    return decorated_function


# ── Routes ───────────────────────────────────────────────────
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        client_ip = request.remote_addr

        if _is_rate_limited(client_ip):
            flash("Too many failed attempts. Please try again in 5 minutes.", "danger")
            return render_template("login.html")

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Please enter both username and password.", "warning")
            return render_template("login.html")

        supabase = get_supabase_client()
        if not supabase:
            flash("Database connection error. Please try again later.", "danger")
            return render_template("login.html")

        try:
            response = (
                supabase.table("admins")
                .select("*")
                .eq("username", username)
                .execute()
            )

            if response.data and len(response.data) > 0:
                stored_hash = response.data[0]["password"]
                if check_password_hash(stored_hash, password):
                    session.permanent = True
                    session["admin_logged_in"] = True
                    session["username"] = username
                    _clear_login_attempts(client_ip)
                    flash("Welcome back, Admin!", "success")
                    return redirect(url_for("dashboard.index"))
                else:
                    _record_failed_login(client_ip)
                    flash("Invalid username or password.", "danger")
            else:
                _record_failed_login(client_ip)
                flash("Invalid username or password.", "danger")
        except Exception as e:
            logger.exception("Login error: %s", e)
            flash("An error occurred. Please try again.", "danger")

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
