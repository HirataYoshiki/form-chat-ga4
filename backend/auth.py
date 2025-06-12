# backend/auth.py
import httpx
import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta # Added timedelta

from backend.config import settings
from backend.db import get_supabase_client # Supabase client for DB access
from supabase import Client # Type hint for Supabase client

logger = logging.getLogger(__name__)

# --- Pydantic Model for Authenticated User ---
class AuthenticatedUser(BaseModel):
    id: str # UUID from Supabase auth.users.id
    app_role: str
    tenant_id: Optional[str] = None # UUID, as string
    email: Optional[str] = None
    full_name: Optional[str] = None

    # Pydantic V2 config
    model_config = ConfigDict(from_attributes=True)

http_bearer_scheme = HTTPBearer(
    description="Supabase JWT token. Obtain it from Supabase Auth client (e.g., supabase-js after login).",
    bearerFormat="JWT" # OpenAPI: format of the bearer token
)

# --- JWKS (JSON Web Key Set) Caching ---
_jwks_cache: Optional[Dict[str, Any]] = None
_jwks_cache_expiry: Optional[datetime] = None
JWKS_CACHE_TTL_SECONDS = 3600 # Cache JWKS for 1 hour

async def get_jwks() -> Dict[str, Any]:
    global _jwks_cache, _jwks_cache_expiry
    now = datetime.utcnow()

    if _jwks_cache and _jwks_cache_expiry and now < _jwks_cache_expiry:
        logger.debug("Using cached JWKS.")
        return _jwks_cache

    if not settings.supabase_jwks_uri:
        logger.error("Supabase JWKS URI is not configured in settings.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication system not configured (JWKS URI missing)."
        )

    logger.info(f"Fetching JWKS from: {settings.supabase_jwks_uri}")
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(settings.supabase_jwks_uri)
            response.raise_for_status() # Raises HTTPStatusError for 4xx/5xx responses
            _jwks_cache = response.json()
            _jwks_cache_expiry = now + timedelta(seconds=JWKS_CACHE_TTL_SECONDS)
            logger.info("Successfully fetched and cached JWKS.")
            return _jwks_cache
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching JWKS: {e.response.status_code} - {e.response.text}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Failed to fetch JWKS: HTTP {e.response.status_code}")
        except Exception as e: # Includes JSONDecodeError, httpx.RequestError, etc.
            logger.error(f"Failed to fetch or parse JWKS: {e}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to process JWKS: {str(e)}")

async def get_current_active_user(
    auth_creds: HTTPAuthorizationCredentials = Depends(http_bearer_scheme), # Gets Bearer token
    supabase_db: Client = Depends(get_supabase_client) # Renamed to avoid clash with 'supabase' var name
) -> AuthenticatedUser:

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or token is invalid/expired.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = auth_creds.credentials # The actual token string

    try:
        jwks = await get_jwks()
        unverified_header = jwt.get_unverified_header(token)
        rsa_key = {}
        for key_dict in jwks.get("keys", []): # Added .get with default
            if key_dict.get("kid") == unverified_header.get("kid"): # Added .get
                rsa_key = {
                    "kty": key_dict["kty"], "kid": key_dict["kid"],
                    "use": key_dict["use"], "n": key_dict["n"], "e": key_dict["e"]
                }
                break
        if not rsa_key:
            logger.warning("JWT KID in token header does not match any key in JWKS.")
            raise credentials_exception

        if not settings.supabase_url:
            logger.error("Supabase URL for JWT issuer validation is not configured.")
            raise HTTPException(status_code=500, detail="Auth system config error (issuer URL).")

        expected_issuer = settings.supabase_url + "/auth/v1"

        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            audience=settings.supabase_jwt_audience,
            issuer=expected_issuer
        )

        user_id: Optional[str] = payload.get("sub")
        email_from_jwt: Optional[str] = payload.get("email")
        # Supabase default role for authenticated users
        # auth_role_from_jwt: Optional[str] = payload.get("role")

        if user_id is None:
            logger.warning("User ID (sub) not found in JWT payload.")
            raise credentials_exception

    except JWTError as e:
        logger.warning(f"JWT validation/decoding error: {e}", exc_info=True)
        raise credentials_exception
    except HTTPException: # Re-raise HTTPExceptions from get_jwks or config checks
        raise
    except Exception as e: # Catch any other unexpected error during JWT processing
        logger.error(f"Unexpected error during JWT processing: {e}", exc_info=True)
        raise credentials_exception # Treat as validation failure

    # Fetch app-specific user profile from public.users
    if supabase_db is None:
        logger.error("Supabase client (supabase_db) unavailable for fetching user profile.")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database client unavailable for user profile.")

    try:
        profile_response = supabase_db.table("users").select("app_role, tenant_id, full_name").eq("id", user_id).maybe_single().execute()

        user_profile = profile_response.data
        if not user_profile:
            logger.warning(f"User profile not found in public.users for user_id: {user_id}. A profile should be created automatically on new user signup.")
            # Depending on policy, could create a default user object here or deny access.
            # For now, deny access if no profile, as tenant_id and app_role are crucial.
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User profile incomplete or not found.")

    except Exception as e:
        logger.error(f"Database error fetching user profile for user_id {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not fetch user profile details.")

    return AuthenticatedUser(
        id=user_id,
        app_role=user_profile.get("app_role", "user"), # Default to 'user' if somehow missing
        tenant_id=str(user_profile.get("tenant_id")) if user_profile.get("tenant_id") else None,
        email=email_from_jwt, # Email from JWT is generally more reliable/verified
        full_name=user_profile.get("full_name")
    )
