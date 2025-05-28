from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import logging
from typing import Optional

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

# --- API Endpoints ---

@app.post("/submit")
async def handle_form_submission(payload: ContactFormPayload):
    logger.info(f"Received form submission: {payload.dict()}")
    return {"status": "success", "message": "Form data received successfully"}

@app.post("/chat", response_model=ChatResponse)
async def handle_chat(payload: ChatMessage):
    logger.info(f"Received chat message: '{payload.message}', session_id: {payload.session_id}")
    
    # Call the placeholder function in ai_agent.py
    agent_reply, response_session_id = ai_agent.get_chat_response(
        message=payload.message, 
        session_id=payload.session_id
    )
    
    return ChatResponse(reply=agent_reply, session_id=response_session_id)

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
