# backend/services/submission_service.py
import logging
from typing import Optional, Dict, Any, Tuple, List # Added Tuple, List
from supabase import Client
from datetime import date, time, datetime # Added date, time, datetime

logger = logging.getLogger(__name__)
CONTACT_SUBMISSIONS_TABLE = "contact_submissions"

async def update_submission_status(
    db: Client,
    tenant_id: str,
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
            .eq("tenant_id", tenant_id) # Add tenant_id filter
            .execute()
        )

        if response.data and len(response.data) > 0:
            logger.info(f"Submission status updated for tenant_id: {tenant_id}, id: {submission_id} to '{new_status}'. Reason: '{reason if reason else 'N/A'}'")
            return response.data[0]
        else:
            logger.warning(
                f"Failed to update submission status for tenant_id: {tenant_id}, id: {submission_id}. Record not found or no data returned. "
                f"Supabase response: {response.model_dump_json() if hasattr(response, 'model_dump_json') else str(response)}"
            )
            return None
    except Exception as e:
        logger.error(f"Exception updating submission status for tenant_id: {tenant_id}, id: {submission_id}: {e}", exc_info=True)
        return None

async def list_submissions(
    db: Client,
    tenant_id: str, # Added tenant_id
    skip: int = 0,
    limit: int = 20,
    form_id: Optional[str] = None,
    submission_status: Optional[str] = None,
    email: Optional[str] = None,
    name: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    sort_by: Optional[str] = "created_at", # Default sort
    sort_order: Optional[str] = "desc",   # Default order
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Lists contact submissions for a specific tenant with filtering, pagination, and sorting.
    Returns a tuple of (list of submission records as dictionaries, total_count).
    Note: The Supabase client's execute() method is synchronous. For true async
    behavior in a FastAPI async endpoint, this should be run in a thread pool
    (e.g., using fastapi.concurrency.run_in_threadpool).
    """
    try:
        query = db.table(CONTACT_SUBMISSIONS_TABLE).select("*", count="exact").eq("tenant_id", tenant_id)

        # Apply other filters
        if form_id:
            query = query.eq("form_id", form_id)
        if submission_status:
            query = query.eq("submission_status", submission_status)
        if email:
            query = query.ilike("email", f"%{email}%")
        if name:
            query = query.ilike("name", f"%{name}%")

        if start_date:
            # Combine with min time and convert to ISO format string for Supabase
            start_datetime_iso = datetime.combine(start_date, time.min).isoformat()
            query = query.gte("created_at", start_datetime_iso)
        if end_date:
            # Combine with max time and convert to ISO format string
            end_datetime_iso = datetime.combine(end_date, time.max).isoformat()
            query = query.lte("created_at", end_datetime_iso)

        # Apply sorting
        # Ensure sort_by is a valid column name to prevent injection-like issues if it were user-supplied without validation.
        # Here, it's from a Query(enum=[...]) in the router, so it's relatively safe.
        if sort_by and sort_order:
            is_ascending = sort_order.lower() == "asc"
            query = query.order(sort_by, desc=not is_ascending)

        # Apply pagination
        # Supabase range is inclusive for 'to', so skip + limit - 1
        query = query.range(skip, skip + limit - 1)

        # Execute the query (synchronous call)
        response = query.execute()

        submissions = response.data if response.data else []
        total_count = response.count if response.count is not None else 0 # Get total count from 'exact'

        logger.debug(f"Listed {len(submissions)} submissions for tenant_id {tenant_id} (skip={skip}, limit={limit}) with total_count {total_count} matching criteria.")
        return submissions, total_count

    except Exception as e:
        logger.error(f"Exception listing submissions for tenant_id {tenant_id} with criteria (form_id={form_id}, status={submission_status}, etc.): {e}", exc_info=True)
        return [], 0
