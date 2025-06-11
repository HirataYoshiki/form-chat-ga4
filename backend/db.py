# backend/db.py
import logging
from typing import Optional
from supabase import create_client, Client
from backend.config import settings # Assuming .config is correct relative path

logger = logging.getLogger(__name__)

supabase_url: Optional[str] = settings.supabase_url
supabase_key: Optional[str] = settings.supabase_service_role_key

supabase_client: Optional[Client] = None

if supabase_url and supabase_key:
    try:
        supabase_client = create_client(supabase_url, supabase_key)
        logger.info("Supabase client initialized successfully.")
    except Exception as e:
        logger.error("Failed to initialize Supabase client: %s", e, exc_info=True)
        supabase_client = None
else:
    logger.warning("Supabase URL or Service Role Key is not set in .env. Supabase client cannot be initialized.")

def get_supabase_client() -> Optional[Client]:
    return supabase_client
