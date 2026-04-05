# File: database_modules/supabase_client.py
"""
Supabase client singleton. Provides a single, reusable database connection
across the entire application.
"""
import logging
import os
from typing import Optional

from dotenv import load_dotenv
from supabase import Client, create_client

logger = logging.getLogger(__name__)

# Ensure .env is loaded from project root irrespective of CWD
_current_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_current_dir)
load_dotenv(os.path.join(_project_root, ".env"))

# Supabase credentials
SUPABASE_URL: str = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY: str = os.environ.get("SUPABASE_KEY", "")

# Singleton instance
_client: Optional[Client] = None


def get_supabase_client() -> Optional[Client]:
    """
    Return a singleton Supabase client instance.

    Returns ``None`` and logs an error when credentials are missing or the
    connection cannot be established.
    """
    global _client

    if _client is not None:
        return _client

    if (
        not SUPABASE_URL
        or "YOUR_SUPABASE_URL_HERE" in SUPABASE_URL
        or not SUPABASE_KEY
        or "YOUR_SUPABASE_KEY_HERE" in SUPABASE_KEY
    ):
        logger.error("Supabase credentials not set in .env file or environment variables.")
        return None

    try:
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Supabase client initialised successfully.")
        return _client
    except Exception as e:
        logger.exception("Error initialising Supabase client: %s", e)
        return None
