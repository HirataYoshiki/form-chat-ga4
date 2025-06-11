from fastapi import FastAPI, Depends, HTTPException, status # Added Depends, HTTPException, status
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import logging
from typing import List, Optional, Any # Added Optional, List, Any
from datetime import date # Added date
from sqlalchemy.orm import Session # Added Session

# Import the AI agent module
from . import ai_agent

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

# --- Models for /chat endpoint ---
class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str
    session_id: Optional[str] = None
    require_form_after_message: bool = False # New field

# --- API Endpoints ---

@app.post("/submit")
async def handle_form_submission(payload: ContactFormPayload):
    logger.info(f"Received form submission: {payload.dict()}")
    return {"status": "success", "message": "Form data received successfully"}

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
def get_db():
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
    yield None

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
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_active_user)
):
    """
    Get the count of submissions based on optional filters (start_date, end_date, form_id).
    Requires authentication.
    """
    if db is None:
        # This check is for the mock get_db. A real get_db would provide a session or fail.
        logger.error("Database session is not available for /api/v1/analytics/submissions/count")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service not configured or unavailable."
        )

    # Construct SubmissionsCountParams from individual query parameters for the response
    request_params = SubmissionsCountParams(start_date=start_date, end_date=end_date, form_id=form_id)

    try:
        count = analytics_service.get_submissions_count(
            db=db, start_date=start_date, end_date=end_date, form_id=form_id
        )
        return SubmissionsCountResponse(count=count, parameters=request_params)
    except Exception as e:
        logger.error(f"Error in get_submissions_count_endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error processing submission count.")


@app.get("/api/v1/analytics/submissions/summary_by_form", response_model=SubmissionsSummaryResponse, tags=["Analytics"])
async def get_submissions_summary_by_form_endpoint(
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_active_user)
):
    """
    Get a summary of submission counts grouped by form_id.
    Requires authentication.
    """
    if db is None:
        logger.error("Database session is not available for /api/v1/analytics/submissions/summary_by_form")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service not configured or unavailable."
        )

    try:
        summary_data_dicts = analytics_service.get_summary_by_form(db=db)
        # summary_data_dicts is List[Dict[str, Any]]
        # Pydantic will validate and convert this to List[FormSummaryItem]
        # when creating SubmissionsSummaryResponse.
        return SubmissionsSummaryResponse(summary=summary_data_dicts)
    except Exception as e:
        logger.error(f"Error in get_submissions_summary_by_form_endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error processing submission summary.")
