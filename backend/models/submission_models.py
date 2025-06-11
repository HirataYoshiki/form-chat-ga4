# backend/models/submission_models.py
from pydantic import BaseModel, Field
from typing import Optional

class SubmissionStatusUpdatePayload(BaseModel):
    """
    Payload for updating the status of a submission.
    """
    new_status: str = Field(
        ...,
        min_length=1,
        description="The new status to set for the submission (e.g., 'contacted', 'converted', 'spam'). This should match one of the predefined status values."
    )
    reason: Optional[str] = Field(
        None,
        description="An optional reason for this status change, especially for statuses like 'unconverted' or 'disqualified'."
    )

# Note: The response for a status update will likely be the full updated submission,
# which can reuse the existing `SubmissionResponse` model defined in `backend.contact_api`.
# Therefore, a specific response model for status updates might not be needed here.
