import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# -------------------------------------------------------------------------
# ⚠️  CRITICAL: Replace these with your actual Supabase URL and Key
# -------------------------------------------------------------------------
# You can also set these as environment variables: SUPABASE_URL and SUPABASE_KEY

SUPABASE_URL = os.environ.get("SUPABASE_URL", "YOUR_SUPABASE_URL_HERE")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "YOUR_SUPABASE_KEY_HERE")

def get_supabase_client() -> Client:
    if not SUPABASE_URL or "YOUR_SUPABASE_URL_HERE" in SUPABASE_URL or not SUPABASE_KEY or "YOUR_SUPABASE_KEY_HERE" in SUPABASE_KEY:
        print("❌ Error: Supabase credentials not set in .env file or environment variables.")
        return None
        
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        return supabase
    except Exception as e:
        print(f"❌ Error initializing Supabase client: {e}")
        return None
