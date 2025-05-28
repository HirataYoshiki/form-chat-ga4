from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Contact Form API", version="0.1.0")

# Add CORS middleware
# This is crucial for allowing the frontend (potentially on a different domain/port)
# to communicate with this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for simplicity in this example
    allow_credentials=True,
    allow_methods=["POST", "GET", "OPTIONS"],  # Specify methods or use ["*"] for all
    allow_headers=["*"],  # Allows all headers
)

class ContactFormPayload(BaseModel):
    name: str
    email: str
    message: str
    ga_client_id: str | None = None
    ga_session_id: str | None = None

@app.post("/submit")
async def handle_form_submission(payload: ContactFormPayload):
    """
    Handles the submission of the contact form.
    It logs the received data and returns a success message.
    In a real application, this is where you would:
    1. Validate the data further (if needed beyond Pydantic).
    2. Save the data to a database.
    3. Send email notifications.
    4. Integrate with other services (e.g., CRM, RAG).
    """
    logger.info(f"Received form submission: {payload.dict()}")
    # Simulate processing or saving data
    # For example, you could add:
    # db_save_status = await save_to_database(payload)
    # if not db_save_status:
    #     raise HTTPException(status_code=500, detail="Failed to save form submission")

    return {"status": "success", "message": "Form data received successfully"}

@app.get("/")
async def read_root():
    """
    Root endpoint to check if the API is running.
    """
    return {"message": "Contact Form API is running. Submit contact data to /submit"}

# To run this app (for development, from the project root directory):
# uvicorn backend.contact_api:app --reload --port 8000
#
# Example of how to test the endpoint with curl:
# curl -X POST "http://localhost:8000/submit" \
# -H "Content-Type: application/json" \
# -d '{
#   "name": "John Doe",
#   "email": "john.doe@example.com",
#   "message": "Hello, I have a question!",
#   "ga_client_id": "ga_client_123",
#   "ga_session_id": "ga_session_456"
# }'
#
# If you want to run it directly for some reason (not typical for FastAPI apps):
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)
