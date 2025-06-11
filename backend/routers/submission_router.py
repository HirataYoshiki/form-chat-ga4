# backend/routers/submission_router.py
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Path, Query # Added Query
from typing import Optional, Any, Dict, List # Added List
from datetime import date # Added date
from supabase import Client

from backend.db import get_supabase_client
from backend.models.submission_models import SubmissionStatusUpdatePayload, SubmissionListResponse # Added SubmissionListResponse
from backend.contact_api import SubmissionResponse as SubmissionItemResponse # Reusing existing model from contact_api and aliasing

# Import services
from backend.services import submission_service
from backend.services import form_ga_config_service
from backend.services import ga4_mp_service

# Attempt to import get_current_active_user from contact_api.py
try:
    from backend.contact_api import get_current_active_user
except ImportError:
    async def get_current_active_user() -> Any: # Dummy for subtask if import fails
        logging.warning("Using dummy get_current_active_user in submission_router.py")
        return {"username": "dummy_auth_user_submission_router"}

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/submissions",
    tags=["Submission Status Management"],
    dependencies=[Depends(get_current_active_user)]
)

# Mapping of submission statuses to GA4 event details
# This could also live in a config file or a dedicated module if it grows.
STATUS_TO_GA4_EVENT_MAP: Dict[str, Dict[str, Any]] = {
    "contacted": {"name": "working_lead", "params_template": {"lead_status": "contacted"}},
    "qualified": {"name": "qualify_lead", "params_template": {}},
    "converted": {"name": "close_convert_lead", "params_template": {}}, # transaction_id to be added dynamically
    "unconverted": {"name": "lead_unconverted", "params_template": {}}, # Custom event
    "disqualified": {"name": "lead_disqualified", "params_template": {}}, # Custom event
}

CONTACT_SUBMISSIONS_TABLE = "contact_submissions" # Define table name constant

@router.patch("/{submission_id}/status", response_model=SubmissionItemResponse) # Use alias for clarity if needed, or SubmissionResponse
async def update_submission_status_endpoint(
    submission_id: int = Path(..., title="The ID of the submission to update", ge=1),
    payload: SubmissionStatusUpdatePayload,
    supabase: Client = Depends(get_supabase_client)
    # current_user is handled by router dependency
):
    if supabase is None:
        logger.error("Supabase client unavailable for PATCH /submissions/.../status")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Supabase client unavailable")

    # 1. Fetch current submission to get original_status, form_id, ga_client_id, ga_session_id
    try:
        # Using .select() with specific columns for efficiency
        query = supabase.table(CONTACT_SUBMISSIONS_TABLE)                      .select("id, form_id, ga_client_id, ga_session_id, submission_status")                      .eq("id", submission_id)                      .single() # Expects one row or raises error if not found / multiple
        current_submission_response = query.execute()

        if not current_submission_response.data: # Check if data exists
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Submission with id {submission_id} not found.")
        current_submission = current_submission_response.data
        original_status = current_submission.get("submission_status")

    except Exception as e_fetch: # Catch potential errors from .single() if not found, or other DB errors
        logger.error(f"Failed to fetch submission {submission_id} before status update: {e_fetch}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve submission details for id {submission_id}.")

    # 2. Update the submission status
    updated_submission_dict = await submission_service.update_submission_status(
        db=supabase,
        submission_id=submission_id,
        new_status=payload.new_status,
        reason=payload.reason
    )

    if not updated_submission_dict:
        logger.error(f"Update_submission_status service failed for submission_id: {submission_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Failed to update submission status for id {submission_id}, record may not exist or update failed.")

    # 3. Send GA4 event if status actually changed and is mapped
    if original_status != payload.new_status and payload.new_status in STATUS_TO_GA4_EVENT_MAP:
        form_id = current_submission.get("form_id")
        ga_client_id = current_submission.get("ga_client_id")

        if form_id and ga_client_id:
            ga_config_dict = form_ga_config_service.get_ga_configuration(supabase, form_id)

            if ga_config_dict:
                api_secret = ga_config_dict.get("ga4_api_secret")
                measurement_id = ga_config_dict.get("ga4_measurement_id")

                if api_secret and measurement_id:
                    event_config = STATUS_TO_GA4_EVENT_MAP[payload.new_status]
                    event_params = {**event_config["params_template"]}

                    event_params["value"] = 0
                    event_params["currency"] = "JPY"

                    event_params["form_id"] = form_id
                    if current_submission.get("ga_session_id"):
                        event_params["session_id"] = current_submission.get("ga_session_id")
                    if payload.new_status == "converted":
                        event_params["transaction_id"] = str(submission_id)

                    ga4_event_payload = {"name": event_config["name"], "params": event_params}

                    logger.info(
                        f"Attempting to send GA4 event '{ga4_event_payload['name']}' for submission_id: {submission_id}, new_status: {payload.new_status}"
                    )
                    try:
                        await ga4_mp_service.send_ga4_event(
                            api_secret=api_secret,
                            measurement_id=measurement_id,
                            client_id=ga_client_id,
                            events=[ga4_event_payload]
                        )
                    except Exception as e_ga:
                        logger.error(
                            f"Unhandled error when trying to send GA4 event for submission_id {submission_id} (status {payload.new_status}): {e_ga}",
                            exc_info=True
                        )
                else:
                    logger.warning(f"GA4 API secret or Measurement ID missing in config for form_id '{form_id}'. Cannot send '{payload.new_status}' event for submission {submission_id}.")
            else:
                logger.warning(f"GA4 configuration not found for form_id '{form_id}'. Cannot send '{payload.new_status}' event for submission {submission_id}.")
        else:
            logger.info(f"Skipping GA4 '{payload.new_status}' event: form_id or ga_client_id missing for submission {submission_id}.")

    return SubmissionItemResponse(**updated_submission_dict)


@router.get("", response_model=SubmissionListResponse, tags=["Submissions Data"])
async def list_submissions_endpoint(
    form_id: Optional[str] = Query(None, description="Filter by form_id."),
    submission_status: Optional[str] = Query(None, description="Filter by submission status."),
    email: Optional[str] = Query(None, description="Filter by email (case-insensitive, partial match)."),
    name: Optional[str] = Query(None, description="Filter by name (case-insensitive, partial match)."),
    start_date: Optional[date] = Query(None, description="Filter by creation date (start of range, YYYY-MM-DD)."),
    end_date: Optional[date] = Query(None, description="Filter by creation date (end of range, YYYY-MM-DD)."),
    skip: int = Query(0, ge=0, description="Number of records to skip."),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records to return."),
    sort_by: Optional[str] = Query("created_at", enum=["created_at", "updated_at", "name", "submission_status", "id", "email", "form_id"], description="Column to sort by."),
    sort_order: Optional[str] = Query("desc", enum=["asc", "desc"], description="Sort order (asc or desc)."),
    supabase: Client = Depends(get_supabase_client)
):
    if supabase is None:
        logger.error("Supabase client unavailable for GET /api/v1/submissions")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Supabase client unavailable")

    try:
        submissions_list_dicts, total_count = await submission_service.list_submissions(
            db=supabase,
            skip=skip,
            limit=limit,
            form_id=form_id,
            submission_status=submission_status,
            email=email,
            name=name,
            start_date=start_date,
            end_date=end_date,
            sort_by=sort_by,
            sort_order=sort_order
        )

        parsed_submissions = [SubmissionItemResponse(**item) for item in submissions_list_dicts]

        return SubmissionListResponse(
            submissions=parsed_submissions,
            total_count=total_count,
            skip=skip,
            limit=limit
        )
    except Exception as e:
        logger.error(f"Error listing submissions: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to list submissions.")
