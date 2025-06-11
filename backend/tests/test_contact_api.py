import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone # Added timezone for created_at comparison
from typing import Optional, Dict, Any, List

# Attempt to import app and models from the correct location
# This assumes tests are run from a context where 'backend' is a discoverable module
try:
    from backend.contact_api import app
    from backend.db import get_supabase_client # For patching
    from backend.contact_api import ContactFormPayload # For type hints if needed, though not strictly for dicts
except ImportError:
    # Fallback for subtask execution if direct import fails
    from contact_api import app # type: ignore
    from db import get_supabase_client # type: ignore
    from contact_api import ContactFormPayload # type: ignore

client = TestClient(app)

# --- Helper Function for Payload ---
def get_valid_payload_dict(form_id: Optional[str] = "test-form-123") -> Dict[str, Any]:
    return {
        "name": "Test User",
        "email": "test@example.com",
        "message": "This is a test message.",
        "ga_client_id": "ga-client-id-example",
        "ga_session_id": "ga-session-id-example",
        "form_id": form_id,
    }

# --- Test Cases ---

def test_submit_form_success_sends_ga4_event_when_configured(mocker): # Renamed
    payload = get_valid_payload_dict() # This includes form_id and ga_client_id

    mock_supabase_client = MagicMock()
    mock_insert_response = MagicMock()
    mock_created_at_iso = datetime.now(timezone.utc).isoformat()
    inserted_record_data = {**payload, "id": 1, "created_at": mock_created_at_iso}
    mock_insert_response.data = [inserted_record_data]
    mock_supabase_client.table.return_value.insert.return_value.execute.return_value = mock_insert_response

    # Mock GA4 services
    mock_get_ga_config = mocker.patch("backend.contact_api.form_ga_config_service.get_ga_configuration")
    mock_send_ga4_event = mocker.patch("backend.contact_api.ga4_mp_service.send_ga4_event")

    mock_ga_config_data = {
        "form_id": payload["form_id"],
        "ga4_measurement_id": "G-VALIDMEASUREMENTID",
        "ga4_api_secret": "validapisecret"
    }
    mock_get_ga_config.return_value = mock_ga_config_data
    mock_send_ga4_event.return_value = True # Simulate successful send

    with patch("backend.contact_api.get_supabase_client", return_value=mock_supabase_client):
        response = client.post("/submit", json=payload)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["id"] == 1

    mock_supabase_client.table.return_value.insert.assert_called_once_with([payload])

    # Assert GA4 mocks
    mock_get_ga_config.assert_called_once_with(mock_supabase_client, payload["form_id"])

    expected_event_params = {
        "event_category": "contact_form",
        "event_label": payload["form_id"],
        "session_id": payload["ga_session_id"]
    }
    mock_send_ga4_event.assert_called_once_with(
        api_secret=mock_ga_config_data["ga4_api_secret"],
        measurement_id=mock_ga_config_data["ga4_measurement_id"],
        client_id=payload["ga_client_id"],
        events=[{"name": "generate_lead", "params": expected_event_params}]
    )

def test_submit_form_success_minimal_fields_skips_ga4_event(mocker): # Updated name and assertions
    minimal_payload = {
        "name": "Minimal User",
        "email": "minimal@example.com",
        "message": "Minimal message.",
    }
    # form_id, ga_client_id, ga_session_id are omitted, will default to None

    mock_supabase_client = MagicMock()
    mock_insert_response = MagicMock()
    mock_created_at_iso = datetime.now(timezone.utc).isoformat()
    data_as_inserted = {
        "name": "Minimal User", "email": "minimal@example.com", "message": "Minimal message.",
        "ga_client_id": None, "ga_session_id": None, "form_id": None
    }
    inserted_record_data = {**data_as_inserted, "id": 2, "created_at": mock_created_at_iso}
    mock_insert_response.data = [inserted_record_data]
    mock_supabase_client.table.return_value.insert.return_value.execute.return_value = mock_insert_response

    # Mock GA4 services to ensure they are NOT called
    mock_get_ga_config = mocker.patch("backend.contact_api.form_ga_config_service.get_ga_configuration")
    mock_send_ga4_event = mocker.patch("backend.contact_api.ga4_mp_service.send_ga4_event")

    with patch("backend.contact_api.get_supabase_client", return_value=mock_supabase_client):
        response = client.post("/submit", json=minimal_payload)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["name"] == "Minimal User"
    assert response_data["id"] == 2
    assert response_data["form_id"] is None
    assert response_data["ga_client_id"] is None

    mock_supabase_client.table.return_value.insert.assert_called_once_with([data_as_inserted])

    # Assert GA4 mocks were NOT called
    mock_get_ga_config.assert_not_called()
    mock_send_ga4_event.assert_not_called()


def test_submit_form_success_ga4_config_not_found_skips_event(mocker):
    payload = get_valid_payload_dict() # This includes form_id and ga_client_id

    mock_supabase_client = MagicMock()
    mock_insert_response = MagicMock()
    mock_created_at_iso = datetime.now(timezone.utc).isoformat()
    inserted_record_data = {**payload, "id": 3, "created_at": mock_created_at_iso}
    mock_insert_response.data = [inserted_record_data]
    mock_supabase_client.table.return_value.insert.return_value.execute.return_value = mock_insert_response

    # Mock GA4 services
    mock_get_ga_config = mocker.patch("backend.contact_api.form_ga_config_service.get_ga_configuration")
    mock_send_ga4_event = mocker.patch("backend.contact_api.ga4_mp_service.send_ga4_event")

    mock_get_ga_config.return_value = None # Simulate GA4 config not found

    with patch("backend.contact_api.get_supabase_client", return_value=mock_supabase_client):
        response = client.post("/submit", json=payload)

    assert response.status_code == 200
    assert response.json()["id"] == 3

    mock_get_ga_config.assert_called_once_with(mock_supabase_client, payload["form_id"])
    mock_send_ga4_event.assert_not_called()


def test_submit_form_supabase_client_unavailable(mocker):
    with patch("backend.contact_api.get_supabase_client", return_value=None):
        response = client.post("/submit", json=get_valid_payload_dict())

    assert response.status_code == 503
    assert response.json() == {"detail": "Database service is currently unavailable. Please try again later."}

def test_submit_form_supabase_insert_api_error(mocker): # Renamed for clarity (APIError from Supabase)
    mock_supabase_client = MagicMock()
    # Simulate an error from Supabase client, e.g., PostgrestAPIError
    # For simplicity, just making execute raise a generic Exception here.
    # A more specific Supabase exception could be mocked if needed.
    mock_supabase_client.table.return_value.insert.return_value.execute.side_effect = Exception("Supabase DB error")

    with patch("backend.contact_api.get_supabase_client", return_value=mock_supabase_client):
        response = client.post("/submit", json=get_valid_payload_dict())

    assert response.status_code == 500
    # The detail message in endpoint is generic for non-HTTPExceptions
    assert response.json() == {"detail": "An error occurred while processing your request."}


def test_submit_form_supabase_insert_returns_no_data(mocker):
    mock_supabase_client = MagicMock()
    mock_empty_response = MagicMock()
    mock_empty_response.data = [] # Supabase returns empty data list
    mock_supabase_client.table.return_value.insert.return_value.execute.return_value = mock_empty_response

    with patch("backend.contact_api.get_supabase_client", return_value=mock_supabase_client):
        response = client.post("/submit", json=get_valid_payload_dict())

    assert response.status_code == 500
    assert response.json() == {"detail": "Failed to save submission: No data returned from database operation."}

def test_submit_form_missing_required_field_name(client): # More specific test name
    # 'name' is a required field in ContactFormPayload
    invalid_payload_missing_name = {
        "email": "invalid@example.com",
        "message": "Message for submission missing name.",
        "form_id": "form-no-name"
    }
    response = client.post("/submit", json=invalid_payload_missing_name)
    assert response.status_code == 422 # FastAPI validation error
    response_data = response.json()
    assert "detail" in response_data
    # Check if 'name' field is reported as missing
    field_error_found = False
    for error in response_data["detail"]:
        if error.get("type") == "missing" and "name" in error.get("loc", []):
            field_error_found = True
            break
    assert field_error_found, "Error detail for missing 'name' field not found."
