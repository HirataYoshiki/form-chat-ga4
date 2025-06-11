# backend/services/submission_service.py
import logging
from typing import Optional, Dict, Any
from supabase import Client
# from datetime import datetime, timezone # Not manually updating updated_at in this version

logger = logging.getLogger(__name__)
CONTACT_SUBMISSIONS_TABLE = "contact_submissions"

async def update_submission_status(
    db: Client,
    submission_id: int,
    new_status: str,
    reason: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Updates the 'submission_status' and 'status_change_reason' for a contact submission.

    It's assumed that an 'updated_at' field in the 'contact_submissions' table
    is handled by a database trigger or will be addressed in a separate schema update.
    This function does not explicitly set 'updated_at'.

    Args:
        db: Supabase client instance.
        submission_id: The ID of the submission to update.
        new_status: The new status string.
        reason: Optional reason for the status change. If None, the reason field
                in the database will be set to NULL (or cleared).

    Returns:
        A dictionary representing the updated submission record if successful,
        otherwise None.
    """
    try:
        update_data: Dict[str, Any] = {"submission_status": new_status}

        # Set status_change_reason, explicitly setting to None if reason is not provided
        # to ensure it clears any existing reason in the DB.
        update_data["status_change_reason"] = reason

        response = (
            db.table(CONTACT_SUBMISSIONS_TABLE)
            .update(update_data)
            .eq("id", submission_id)
            .execute()
        )

        # Supabase update typically returns the updated record(s) in response.data
        if response.data and len(response.data) > 0:
            logger.info(f"Submission status updated for id: {submission_id} to '{new_status}'. Reason: '{reason if reason else 'N/A'}'")
            return response.data[0]
        else:
            # This branch might be hit if the record with submission_id doesn't exist,
            # or if RLS prevents the update and returns no data.
            logger.warning(
                f"Failed to update submission status for id: {submission_id}. Record not found or no data returned from update. "
                f"Supabase response: {response.model_dump_json() if hasattr(response, 'model_dump_json') else str(response)}"
            )
            return None
    except Exception as e:
        logger.error(f"Exception updating submission status for id {submission_id}: {e}", exc_info=True)
        return None
