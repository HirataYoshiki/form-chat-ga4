# backend/tests/test_submission_api.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch, ANY as AnyMockValue
from datetime import datetime, timezone, date # Ensure date is imported
from typing import Optional, Dict, Any, List

# Attempt to import app and other necessary components
try:
    from backend.contact_api import app
    # For patching, paths are relative to where they are called in the router/service
except ImportError:
    from contact_api import app # type: ignore

client = TestClient(app)

# --- Mock Data & Helpers ---
SUBMISSIONS_API_BASE_PATH = "/api/v1/submissions" # Renamed for clarity
TEST_SUBMISSION_ID = 123
MOCK_AUTH_USER = {"username": "test_submission_user"}

def helper_mock_submission_dict(
    submission_id: int = TEST_SUBMISSION_ID,
    form_id: str = "form-xyz",
    ga_client_id: Optional[str] = "client-id-123",
    ga_session_id: Optional[str] = "session-id-456",
    current_status: str = "new",
    reason: Optional[str] = None
) -> Dict[str, Any]:
    return {
        "id": submission_id,
        "name": "Original Test Name",
        "email": "test.user@example.com",
        "message": "This is an original test message.",
        "ga_client_id": ga_client_id,
        "ga_session_id": ga_session_id,
        "form_id": form_id,
        "submission_status": current_status,
        "status_change_reason": reason,
        "created_at": datetime(2023, 1, 10, 10, 0, 0, tzinfo=timezone.utc).isoformat(),
        "updated_at": datetime(2023, 1, 10, 11, 0, 0, tzinfo=timezone.utc).isoformat(),
    }

def helper_mock_ga_config_dict(form_id: str = "form-xyz") -> Dict[str, Any]:
    return {
        "form_id": form_id,
        "ga4_measurement_id": "G-GA4VALIDID",
        "ga4_api_secret": "valid_secret_for_ga4",
        "description": "GA Config for " + form_id,
        "created_at": datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc).isoformat(),
        "updated_at": datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc).isoformat(),
    }

# --- Test Cases for PATCH /api/v1/submissions/{submission_id}/status ---

@patch("backend.routers.submission_router.get_current_active_user", return_value=MOCK_AUTH_USER)
@patch("backend.routers.submission_router.get_supabase_client")
@patch("backend.services.submission_service.update_submission_status")
@patch("backend.services.form_ga_config_service.get_ga_configuration")
@patch("backend.services.ga4_mp_service.send_ga4_event")
def test_update_status_success_sends_ga4_event_for_converted(
    mock_send_ga4_event, mock_get_ga_config, mock_update_status_svc, mock_get_supabase, mock_auth, client
):
    new_status = "converted"
    payload = {"new_status": new_status, "reason": "Customer purchased product X."}

    mock_supabase_instance = MagicMock(name="supabase_mock")
    mock_get_supabase.return_value = mock_supabase_instance

    current_submission = helper_mock_submission_dict(current_status="qualified")
    # Mock the initial fetch of the submission within the endpoint
    mock_supabase_instance.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(data=current_submission)

    updated_submission_from_service = {**current_submission, "submission_status": new_status, "status_change_reason": payload["reason"]}
    mock_update_status_svc.return_value = updated_submission_from_service

    mock_get_ga_config.return_value = helper_mock_ga_config_dict(form_id=current_submission["form_id"])
    mock_send_ga4_event.return_value = True # Simulate GA4 send success

    response = client.patch(f"{SUBMISSIONS_API_BASE_PATH}/{TEST_SUBMISSION_ID}/status", json=payload)

    assert response.status_code == 200
    resp_data = response.json()
    assert resp_data["submission_status"] == new_status
    assert resp_data["status_change_reason"] == payload["reason"]

    mock_update_status_svc.assert_called_once_with(
        db=mock_supabase_instance, submission_id=TEST_SUBMISSION_ID, new_status=new_status, reason=payload["reason"]
    )
    mock_get_ga_config.assert_called_once_with(mock_supabase_instance, current_submission["form_id"])

    expected_ga4_event_name = "close_convert_lead"
    expected_ga4_params = {
        "form_id": current_submission["form_id"],
        "session_id": current_submission["ga_session_id"],
        "transaction_id": str(TEST_SUBMISSION_ID)
    }
    mock_send_ga4_event.assert_called_once_with(
        api_secret=helper_mock_ga_config_dict()["ga4_api_secret"],
        measurement_id=helper_mock_ga_config_dict()["ga4_measurement_id"],
        client_id=current_submission["ga_client_id"],
        events=[{"name": expected_ga4_event_name, "params": expected_ga4_params}]
    )

@patch("backend.routers.submission_router.get_current_active_user", return_value=MOCK_AUTH_USER)
@patch("backend.routers.submission_router.get_supabase_client")
@patch("backend.services.submission_service.update_submission_status")
@patch("backend.services.ga4_mp_service.send_ga4_event") # No need to mock get_ga_config if event not sent
def test_update_status_success_no_ga4_event_if_status_not_mapped(
    mock_send_ga4_event, mock_update_status_svc, mock_get_supabase, mock_auth, client
):
    new_status = "new" # 'new' is not in STATUS_TO_GA4_EVENT_MAP for sending event post-update
    payload = {"new_status": new_status}

    mock_supabase_instance = MagicMock()
    mock_get_supabase.return_value = mock_supabase_instance

    current_submission = helper_mock_submission_dict(current_status="spam")
    mock_supabase_instance.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(data=current_submission)

    updated_submission_from_service = {**current_submission, "submission_status": new_status}
    mock_update_status_svc.return_value = updated_submission_from_service

    response = client.patch(f"{SUBMISSIONS_API_BASE_PATH}/{TEST_SUBMISSION_ID}/status", json=payload)

    assert response.status_code == 200
    assert response.json()["submission_status"] == new_status
    mock_send_ga4_event.assert_not_called()


@patch("backend.routers.submission_router.get_current_active_user", return_value=MOCK_AUTH_USER)
@patch("backend.routers.submission_router.get_supabase_client")
def test_update_status_submission_fetch_fails_404(mock_get_supabase, mock_auth, client):
    payload = {"new_status": "contacted"}
    mock_supabase_instance = MagicMock()
    mock_get_supabase.return_value = mock_supabase_instance

    # Simulate submission not found by initial fetch in router
    mock_supabase_instance.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(data=None)

    response = client.patch(f"{SUBMISSIONS_API_BASE_PATH}/{TEST_SUBMISSION_ID}/status", json=payload)
    assert response.status_code == 404


@patch("backend.routers.submission_router.get_current_active_user", return_value=MOCK_AUTH_USER)
@patch("backend.routers.submission_router.get_supabase_client")
@patch("backend.services.submission_service.update_submission_status")
def test_update_status_service_layer_fails_update(mock_update_status_svc, mock_get_supabase, mock_auth, client):
    payload = {"new_status": "contacted"}
    mock_supabase_instance = MagicMock()
    mock_get_supabase.return_value = mock_supabase_instance

    current_submission = helper_mock_submission_dict()
    mock_supabase_instance.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(data=current_submission)

    mock_update_status_svc.return_value = None # Simulate service layer failing the update

    response = client.patch(f"{SUBMISSIONS_API_BASE_PATH}/{TEST_SUBMISSION_ID}/status", json=payload)
    assert response.status_code == 404 # Changed from 500, as service returning None often means "not found" or "no action"

@patch("backend.routers.submission_router.get_current_active_user", return_value=MOCK_AUTH_USER)
@patch("backend.routers.submission_router.get_supabase_client")
@patch("backend.services.form_ga_config_service.get_ga_configuration")
@patch("backend.services.submission_service.update_submission_status")
@patch("backend.services.ga4_mp_service.send_ga4_event")
def test_update_status_ga4_config_not_found_skips_ga_event(
    mock_send_ga4_event, mock_update_status_svc, mock_get_ga_config, mock_get_supabase, mock_auth, client
):
    new_status = "converted"
    payload = {"new_status": new_status}

    mock_supabase_instance = MagicMock()
    mock_get_supabase.return_value = mock_supabase_instance

    current_submission = helper_mock_submission_dict(current_status="qualified")
    mock_supabase_instance.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(data=current_submission)

    updated_submission_from_service = {**current_submission, "submission_status": new_status}
    mock_update_status_svc.return_value = updated_submission_from_service

    mock_get_ga_config.return_value = None # Simulate GA4 config not found for the form_id

    response = client.patch(f"{SUBMISSIONS_API_BASE_PATH}/{TEST_SUBMISSION_ID}/status", json=payload)

    assert response.status_code == 200
    assert response.json()["submission_status"] == new_status
    mock_send_ga4_event.assert_not_called() # GA4 event should not be sent
    mock_get_ga_config.assert_called_once_with(mock_supabase_instance, current_submission["form_id"])

# --- Test Cases for GET /api/v1/submissions ---

@patch("backend.routers.submission_router.get_current_active_user", return_value=MOCK_AUTH_USER)
@patch("backend.routers.submission_router.get_supabase_client")
@patch("backend.services.submission_service.list_submissions")
def test_list_submissions_success_no_filters(mock_list_svc, mock_get_supabase_dep, mock_auth_dep, client): # Renamed mock args
    mock_supabase_instance = MagicMock(name="supabase_mock_list_no_filter")
    mock_get_supabase_dep.return_value = mock_supabase_instance

    mock_data = [
        helper_mock_submission_dict(submission_id=101, form_id="formA"),
        helper_mock_submission_dict(submission_id=102, form_id="formB"),
    ]
    mock_total = 50 # Example total count larger than returned items for pagination
    mock_list_svc.return_value = (mock_data, mock_total)

    response = client.get(f"{SUBMISSIONS_API_BASE_PATH}/") # Ensure trailing slash for query params

    assert response.status_code == 200
    json_response = response.json()
    assert len(json_response["submissions"]) == 2
    assert json_response["total_count"] == mock_total
    assert json_response["skip"] == 0 # Default skip
    assert json_response["limit"] == 20 # Default limit
    assert json_response["submissions"][0]["id"] == 101

    mock_list_svc.assert_called_once_with(
        db=mock_supabase_instance,
        skip=0, limit=20,
        form_id=None, submission_status=None, email=None, name=None,
        start_date=None, end_date=None,
        sort_by="created_at", sort_order="desc" # Default sort params
    )

@patch("backend.routers.submission_router.get_current_active_user", return_value=MOCK_AUTH_USER)
@patch("backend.routers.submission_router.get_supabase_client")
@patch("backend.services.submission_service.list_submissions")
def test_list_submissions_with_all_filters_pagination_sorting(mock_list_svc, mock_get_supabase_dep, mock_auth_dep, client):
    mock_supabase_instance = MagicMock(name="supabase_mock_list_filters")
    mock_get_supabase_dep.return_value = mock_supabase_instance

    mock_data = [helper_mock_submission_dict(submission_id=201, form_id="form-filter")]
    mock_total = 1
    mock_list_svc.return_value = (mock_data, mock_total)

    params = {
        "form_id": "form-filter", "submission_status": "converted",
        "email": "filter@example.com", "name": "Filter User",
        "start_date": "2024-01-01", "end_date": "2024-01-31",
        "skip": 10, "limit": 5,
        "sort_by": "name", "sort_order": "asc"
    }
    response = client.get(f"{SUBMISSIONS_API_BASE_PATH}/", params=params)

    assert response.status_code == 200
    json_response = response.json()
    assert len(json_response["submissions"]) == 1
    assert json_response["total_count"] == mock_total
    assert json_response["skip"] == 10
    assert json_response["limit"] == 5
    assert json_response["submissions"][0]["id"] == 201

    # FastAPI Query converts date strings to date objects
    # from datetime import date as date_type # For type checking in assert (already imported at top)
    mock_list_svc.assert_called_once_with(
        db=mock_supabase_instance,
        skip=10, limit=5,
        form_id="form-filter", submission_status="converted",
        email="filter@example.com", name="Filter User",
        start_date=date(2024,1,1), end_date=date(2024,1,31),
        sort_by="name", sort_order="asc"
    )

@patch("backend.routers.submission_router.get_current_active_user", return_value=MOCK_AUTH_USER)
@patch("backend.routers.submission_router.get_supabase_client")
@patch("backend.services.submission_service.list_submissions")
def test_list_submissions_empty_result_from_service(mock_list_svc, mock_get_supabase_dep, mock_auth_dep, client):
    mock_supabase_instance = MagicMock(name="supabase_mock_list_empty")
    mock_get_supabase_dep.return_value = mock_supabase_instance
    mock_list_svc.return_value = ([], 0) # Service returns empty list and 0 total

    response = client.get(f"{SUBMISSIONS_API_BASE_PATH}/")
    assert response.status_code == 200
    json_response = response.json()
    assert len(json_response["submissions"]) == 0
    assert json_response["total_count"] == 0

@patch("backend.routers.submission_router.get_current_active_user", return_value=MOCK_AUTH_USER)
@patch("backend.routers.submission_router.get_supabase_client")
def test_list_submissions_supabase_client_is_none(mock_get_supabase_dep, mock_auth_dep, client):
    mock_get_supabase_dep.return_value = None # Simulate Supabase client not available

    response = client.get(f"{SUBMISSIONS_API_BASE_PATH}/")
    assert response.status_code == 503
    assert response.json()["detail"] == "Supabase client unavailable" # Match error detail

@patch("backend.routers.submission_router.get_current_active_user", return_value=MOCK_AUTH_USER)
@patch("backend.routers.submission_router.get_supabase_client")
@patch("backend.services.submission_service.list_submissions")
def test_list_submissions_service_raises_exception(mock_list_svc, mock_get_supabase_dep, mock_auth_dep, client):
    mock_supabase_instance = MagicMock(name="supabase_mock_list_svc_error")
    mock_get_supabase_dep.return_value = mock_supabase_instance
    mock_list_svc.side_effect = Exception("Simulated service error")

    response = client.get(f"{SUBMISSIONS_API_BASE_PATH}/")
    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to list submissions."
