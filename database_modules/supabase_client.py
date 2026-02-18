import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv

# Ensure .env is loaded from project root irrespective of CWD
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
load_dotenv(os.path.join(project_root, '.env'))

# Get Supabase Credentials
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

def get_supabase_client() -> Client:
    if not SUPABASE_URL or "YOUR_SUPABASE_URL_HERE" in SUPABASE_URL or not SUPABASE_KEY or "YOUR_SUPABASE_KEY_HERE" in SUPABASE_KEY:
        print("Error: Supabase credentials not set in .env file or environment variables.")
        return None
        
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        return supabase
    except Exception as e:
        print(f"Error initializing Supabase client: {e}")
        return None
