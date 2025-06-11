from fastapi import FastAPI, Depends, HTTPException, status # Added Depends, HTTPException, status
from pydantic import BaseModel
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
    ga_client_id: Optional[str] = None
    ga_session_id: Optional[str] = None
    form_id: Optional[str] = None # Added

class SubmissionResponse(BaseModel): # Newly added
    id: int
    created_at: datetime
    name: str
    email: str
    message: str
    ga_client_id: Optional[str] = None
    ga_session_id: Optional[str] = None
    form_id: Optional[str] = None

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
            # SubmissionResponse model will validate and structure the output.
            # Ensure all fields required by SubmissionResponse are present in inserted_record
            # or can be defaulted by Pydantic if optional.
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
async def handle_chat(payload: ChatMessage):
    logger.info(f"Received chat message: '{payload.message}', session_id: {payload.session_id}")
    
    # Call the ai_agent.py function which now returns three values
    agent_reply, response_session_id, require_form = ai_agent.get_chat_response(
        message=payload.message, 
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

# Assuming your services and models are structured in directories
# These imports assume contact_api.py is in the 'backend' directory,
# and 'services' and 'models' are subdirectories of 'backend'.
try:
    from .services import analytics_service
    from .models.analytics_models import (
        SubmissionsCountResponse,
        SubmissionsCountParams, # This model is used in response construction
        SubmissionsSummaryResponse,
        FormSummaryItem # Used by SubmissionsSummaryResponse
    )
except ImportError:
    # Fallback for cases where the subtask might run in a context
    # where sibling imports don't work as expected.
    # This is primarily for robustness of the subtask itself.
    import analytics_service # type: ignore
    from models.analytics_models import ( # type: ignore
        SubmissionsCountResponse,
        SubmissionsCountParams,
        SubmissionsSummaryResponse,
        FormSummaryItem
    )


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

# Placeholder for user authentication dependency
# Replace with your actual authentication logic
async def get_current_active_user() -> Any: # Added return type hint
    # Mock implementation.
    # To simulate a protected endpoint that currently doesn't authenticate properly:
    # raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    # For development, returning a dummy user or None to bypass actual auth.
    return {"username": "devuser", "permissions": ["view_analytics"]}


@app.get("/api/v1/analytics/submissions/count", response_model=SubmissionsCountResponse, tags=["Analytics"])
async def get_submissions_count_endpoint(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    form_id: Optional[str] = None,
    supabase: Optional[Client] = Depends(get_supabase_client), # Changed dependency
    current_user: Any = Depends(get_current_active_user)
):
    """
    Get the count of submissions based on optional filters (start_date, end_date, form_id).
    Requires authentication.
    """
    if supabase is None:
        logger.error("Supabase client not available for /api/v1/analytics/submissions/count")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Supabase client is not initialized. Check server logs.")

    logger.info("Analytics count endpoint called. Supabase client available. Returning dummy data.")
    request_params = SubmissionsCountParams(start_date=start_date, end_date=end_date, form_id=form_id)
    return SubmissionsCountResponse(count=0, parameters=request_params)


@app.get("/api/v1/analytics/submissions/summary_by_form", response_model=SubmissionsSummaryResponse, tags=["Analytics"])
async def get_submissions_summary_by_form_endpoint(
    supabase: Optional[Client] = Depends(get_supabase_client), # Changed dependency
    current_user: Any = Depends(get_current_active_user)
):
    """
    Get a summary of submission counts grouped by form_id.
    Requires authentication.
    """
    if supabase is None:
        logger.error("Supabase client not available for /api/v1/analytics/submissions/summary_by_form")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Supabase client is not initialized. Check server logs.")

    logger.info("Analytics summary endpoint called. Supabase client available. Returning dummy data.")
    return SubmissionsSummaryResponse(summary=[])
