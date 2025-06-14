from fastapi import FastAPI, Depends, HTTPException, status # Added Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict # Added ConfigDict
from fastapi.middleware.cors import CORSMiddleware
import logging
from typing import List, Optional, Any # Ensure List, Optional, Any are imported
from datetime import date, datetime # Ensure date and datetime are imported
# Removed: from sqlalchemy.orm import Session
from supabase import Client # Add this import

# Import the AI agent module
from . import ai_agent
from .config import settings # Ensure settings is imported if used directly
from .db import get_supabase_client # Add this import for the new dependency
from .routers import form_ga_config_router, submission_router, tenant_router, rag_router, user_router # Added user_router
from .services import form_ga_config_service # Added import
from .services import ga4_mp_service # Added import
from .auth import AuthenticatedUser, get_current_active_user # Added AuthenticatedUser
from uuid import UUID # For tenant_id type

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Contact Form API with Chat", version="0.2.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)

# --- Models for /submit endpoint ---
class ContactFormPayload(BaseModel):
    name: str
    email: str
    message: str
    tenant_id: str # Added
    ga_client_id: Optional[str] = None
    ga_session_id: Optional[str] = None
    form_id: Optional[str] = None # Added

class SubmissionResponse(BaseModel): # Newly added
    id: int
    created_at: datetime
    name: str
    email: str
    message: str
    tenant_id: str # Added
    ga_client_id: Optional[str] = None
    ga_session_id: Optional[str] = None
    form_id: Optional[str] = None
    submission_status: Optional[str] = None # Assuming this comes from DB
    status_change_reason: Optional[str] = None # Assuming this comes from DB
    updated_at: Optional[datetime] = None # Assuming this comes from DB

    model_config = ConfigDict(from_attributes=True) # Added for consistency/ORM mode

# --- Models for /chat endpoint ---
class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str
    session_id: Optional[str] = None
    require_form_after_message: bool = False # New field

# --- API Endpoints ---

@app.post("/submit", response_model=SubmissionResponse) # Ensure SubmissionResponse is imported
async def handle_form_submission(
    payload: ContactFormPayload,
    supabase: Optional[Client] = Depends(get_supabase_client)
):
    logger.info(f"Received form submission: {payload.model_dump_json()}") # Use model_dump_json for logging Pydantic V2

    if supabase is None:
        logger.error("Supabase client not available for /submit endpoint.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service is currently unavailable. Please try again later."
        )

    try:
        # For Pydantic V2, use model_dump. For V1, use dict.
        # Assuming Pydantic V2 based on pydantic-settings usage earlier.
        data_to_insert = payload.model_dump(exclude_unset=False)

        # Supabase insert expects a list of dicts, even for a single record
        response = supabase.table("contact_submissions").insert([data_to_insert]).execute()

        if response.data and len(response.data) > 0:
            inserted_record = response.data[0]
            logger.info(f"Successfully inserted submission. ID: {inserted_record.get('id')}")

            # --- GA4 generate_lead イベント送信 ---
            if payload.tenant_id and payload.form_id and payload.ga_client_id: # Added tenant_id check
                try:
                    ga_config_dict = form_ga_config_service.get_ga_configuration(
                        supabase,
                        tenant_id=payload.tenant_id, # Pass tenant_id
                        form_id=payload.form_id
                    )
                    if ga_config_dict:
                        api_secret = ga_config_dict.get("ga4_api_secret")
                        measurement_id = ga_config_dict.get("ga4_measurement_id")

                        if api_secret and measurement_id:
                            event_params = {
                                "event_category": "contact_form",
                                "event_label": payload.form_id,
                            }
                            if payload.ga_session_id:
                                event_params["session_id"] = payload.ga_session_id

                            event_params["value"] = 0  # Added
                            event_params["currency"] = "JPY" # Added

                            ga4_event = {"name": "generate_lead", "params": event_params}

                            logger.info(f"Attempting to send generate_lead event to GA4 for form_id: {payload.form_id}, client_id: {payload.ga_client_id}")
                            ga_sent_successfully = await ga4_mp_service.send_ga4_event(
                                api_secret=api_secret,
                                measurement_id=measurement_id,
                                client_id=payload.ga_client_id,
                                events=[ga4_event]
                            )
                            if not ga_sent_successfully:
                                logger.warning(f"generate_lead event sending to GA4 may have failed for form_id: {payload.form_id} (see previous logs from ga4_mp_service).")
                        else:
                            logger.warning(f"GA4 API secret or Measurement ID missing in config for form_id '{payload.form_id}'. Cannot send generate_lead event.")
                    else:
                        logger.warning(f"GA4 configuration not found for tenant_id '{payload.tenant_id}', form_id '{payload.form_id}'. Cannot send generate_lead event.")
                except Exception as e_ga_setup: # Catch errors during GA config fetch or event construction
                    logger.error(f"Error during GA4 event preparation for generate_lead (tenant_id: {payload.tenant_id}, form_id: {payload.form_id}): {e_ga_setup}", exc_info=True)
            else:
                logger.info("Skipping GA4 generate_lead event: tenant_id, form_id or ga_client_id missing from payload for submission ID: %s.", inserted_record.get('id'))
            # --- GA4 イベント送信ここまで ---

            return SubmissionResponse(**inserted_record)
        else:
            # Log the actual response from Supabase for debugging
            logger.error(
                "Supabase insert operation did not return data as expected. Full response: %s",
                response.model_dump_json() if hasattr(response, 'model_dump_json') else str(response)
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save submission: No data returned from database operation."
            )

    except HTTPException: # Re-raise HTTPExceptions directly
        raise
    except Exception as e:
        logger.error(f"Error saving submission to Supabase: {e}", exc_info=True)
        # Avoid leaking detailed error messages to the client in production if not desired.
        # For now, including str(e) for easier debugging during development.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing your request." # str(e) removed for security
        )

@app.post("/chat", response_model=ChatResponse)
async def handle_chat(
    payload: ChatMessage,
    current_user: AuthenticatedUser = Depends(get_current_active_user), # Added authentication
    db: Client = Depends(get_supabase_client) # Added Supabase client dependency
):
    logger.info(f"Received chat message: '{payload.message}', session_id: {payload.session_id}, user_id: {current_user.id}, tenant_id: {current_user.tenant_id}")

    if not current_user.tenant_id:
        logger.warning(f"User {current_user.id} attempted to chat without a tenant_id.")
        # Or, allow chat without RAG if tenant_id is None (e.g. for superuser or general queries)
        # For now, let's assume RAG is primary and requires tenant_id for corpus.
        # If general chat without RAG is allowed for users without tenant_id, this check needs adjustment.
        # raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not associated with a tenant for RAG context.")
        # For now, let's allow the call to proceed, and ai_agent will skip RAG if tenant_id is None.
        # This means the tenant_id parameter in get_chat_response needs to be Optional[uuid.UUID].
        # The prompt for ai_agent.py made it uuid.UUID (required). This is a conflict.
        # I will proceed assuming tenant_id IS required for chat for now, and if not available, it's an issue.
        # This aligns with tenant-scoped RAG.
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Chat requires a user associated with a tenant.")

    if db is None:
        logger.error(f"Supabase client not available for /chat endpoint for user {current_user.id}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database service unavailable.")

    agent_reply, response_session_id, require_form = await ai_agent.get_chat_response(
        message=payload.message,
        tenant_id=UUID(current_user.tenant_id), # Pass tenant_id
        db=db, # Pass Supabase client
        session_id=payload.session_id
    )
    
    return ChatResponse(
        reply=agent_reply, 
        session_id=response_session_id,
        require_form_after_message=require_form # Pass the value from the agent
    )

@app.get("/")
async def read_root():
    return {"message": "Contact Form API with Chat is running. Submit contact data to /submit or chat messages to /chat"}

# To run this app (for development, from the project root directory):
# uvicorn backend.contact_api:app --reload --port 8000
#
# Example of how to test the /chat endpoint with curl:
# curl -X POST "http://localhost:8000/chat" \
# -H "Content-Type: application/json" \
# -d '{
#   "message": "Hello Agent!",
#   "session_id": "user123_chat789"
# }'

# Placeholder for database session dependency
# In a real application, this would be configured with your database connection
# def get_db(): # This function was already removed in a previous step, ensuring it's gone
    # Mock implementation. Replace with your actual database session provider.
    # For example:
    # from .database import SessionLocal # Assuming you have a database.py
    # db = SessionLocal()
    # try:
    #     yield db
    # finally:
    #     db.close()
    # For now, yielding None and endpoints will check for this.
    # A real implementation would yield a SQLAlchemy Session.
    # yield None # Removed stub get_db function

# The get_current_active_user is now imported from backend.auth
# The old placeholder function below is removed.
# async def get_current_active_user() -> Any: # Added return type hint
#     # Mock implementation.
#     # To simulate a protected endpoint that currently doesn't authenticate properly:
#     # raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
#     # For development, returning a dummy user or None to bypass actual auth.
#     # return {"username": "devuser", "permissions": ["view_analytics"]} # Keeping this for now, might be used by other parts or future tests
#     return {"username": "devuser", "permissions": ["view_analytics"]}

app.include_router(form_ga_config_router.router)
app.include_router(submission_router.router)
app.include_router(tenant_router.router)
app.include_router(rag_router.router) # Added rag_router
app.include_router(user_router.router) # Added user_router
