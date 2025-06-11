import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

# Attempt to import app and other necessary components
try:
    from backend.contact_api import app
    # For patching, we need the actual path to the dependency used in the router
    # from backend.db import get_supabase_client # Not directly used if router import is patched
    # from backend.contact_api import get_current_active_user # Same as above
except ImportError:
    from contact_api import app # type: ignore


client = TestClient(app)

# --- Mock Data & Helpers ---
BASE_PATH = "/api/v1/ga_configurations"
TEST_FORM_ID = "test-form-for-ga"
MOCK_USER = {"username": "testuser"}

def mock_ga_config_payload_dict(form_id_override: Optional[str] = None) -> Dict[str, Any]:
    return {
        "form_id": form_id_override or TEST_FORM_ID,
        "ga4_measurement_id": "G-TEST12345",
        "ga4_api_secret": "test_api_secret_value",
        "description": "Test GA4 Configuration"
    }

def mock_db_record_dict(payload: Dict[str, Any]) -> Dict[str, Any]:
    now_iso = datetime.now(timezone.utc).isoformat()
    return {
        **payload,
        "created_at": now_iso,
        "updated_at": now_iso
    }

# --- Test Cases ---

@patch("backend.routers.form_ga_config_router.get_current_active_user", return_value=MOCK_USER)
@patch("backend.routers.form_ga_config_router.get_supabase_client")
@patch("backend.services.form_ga_config_service.create_ga_configuration")
@patch("backend.services.form_ga_config_service.get_ga_configuration") # For pre-check
def test_create_ga_configuration_success(mock_get_config, mock_create_config, mock_get_supabase, mock_auth, client):
    payload = mock_ga_config_payload_dict()

    mock_get_supabase.return_value = MagicMock() # Simulate available Supabase client
    mock_get_config.return_value = None # Simulate no existing config
    mock_create_config.return_value = mock_db_record_dict(payload)

    response = client.post(BASE_PATH, json=payload)

    assert response.status_code == 201
    response_data = response.json()
    assert response_data["form_id"] == TEST_FORM_ID
    assert response_data["ga4_measurement_id"] == "G-TEST12345"
    mock_create_config.assert_called_once()

@patch("backend.routers.form_ga_config_router.get_current_active_user", return_value=MOCK_USER)
@patch("backend.routers.form_ga_config_router.get_supabase_client")
@patch("backend.services.form_ga_config_service.get_ga_configuration")
def test_create_ga_configuration_already_exists(mock_get_config, mock_get_supabase, mock_auth, client):
    payload = mock_ga_config_payload_dict()
    mock_get_supabase.return_value = MagicMock()
    mock_get_config.return_value = mock_db_record_dict(payload) # Simulate existing config

    response = client.post(BASE_PATH, json=payload)

    assert response.status_code == 409

@patch("backend.routers.form_ga_config_router.get_current_active_user", return_value=MOCK_USER)
@patch("backend.routers.form_ga_config_router.get_supabase_client")
@patch("backend.services.form_ga_config_service.get_ga_configuration")
def test_get_ga_configuration_success(mock_get_config, mock_get_supabase, mock_auth, client):
    db_record = mock_db_record_dict(mock_ga_config_payload_dict())
    mock_get_supabase.return_value = MagicMock()
    mock_get_config.return_value = db_record

    response = client.get(f"{BASE_PATH}/{TEST_FORM_ID}")

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["form_id"] == TEST_FORM_ID
    assert response_data["ga4_measurement_id"] == db_record["ga4_measurement_id"]

@patch("backend.routers.form_ga_config_router.get_current_active_user", return_value=MOCK_USER)
@patch("backend.routers.form_ga_config_router.get_supabase_client")
@patch("backend.services.form_ga_config_service.get_ga_configuration")
def test_get_ga_configuration_not_found(mock_get_config, mock_get_supabase, mock_auth, client):
    mock_get_supabase.return_value = MagicMock()
    mock_get_config.return_value = None # Simulate not found

    response = client.get(f"{BASE_PATH}/{TEST_FORM_ID}")

    assert response.status_code == 404

@patch("backend.routers.form_ga_config_router.get_current_active_user", return_value=MOCK_USER)
@patch("backend.routers.form_ga_config_router.get_supabase_client")
@patch("backend.services.form_ga_config_service.list_ga_configurations")
def test_list_ga_configurations_success(mock_list_configs, mock_get_supabase, mock_auth, client):
    mock_get_supabase.return_value = MagicMock()
    payload1 = mock_ga_config_payload_dict(form_id_override="form1")
    payload2 = mock_ga_config_payload_dict(form_id_override="form2")
    db_records = [mock_db_record_dict(payload1), mock_db_record_dict(payload2)]
    mock_list_configs.return_value = db_records

    response = client.get(BASE_PATH)

    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data["configurations"]) == 2
    assert response_data["configurations"][0]["form_id"] == "form1"

@patch("backend.routers.form_ga_config_router.get_current_active_user", return_value=MOCK_USER)
@patch("backend.routers.form_ga_config_router.get_supabase_client")
@patch("backend.services.form_ga_config_service.update_ga_configuration")
def test_update_ga_configuration_success(mock_update_config, mock_get_supabase, mock_auth, client):
    update_payload = {"description": "Updated Test Description"}
    # Original payload for context, though service mock determines outcome
    original_payload = mock_ga_config_payload_dict()
    updated_db_record = mock_db_record_dict({**original_payload, **update_payload})

    mock_get_supabase.return_value = MagicMock()
    mock_update_config.return_value = updated_db_record

    response = client.put(f"{BASE_PATH}/{TEST_FORM_ID}", json=update_payload)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["description"] == "Updated Test Description"
    assert response_data["form_id"] == TEST_FORM_ID
    mock_update_config.assert_called_once()

@patch("backend.routers.form_ga_config_router.get_current_active_user", return_value=MOCK_USER)
@patch("backend.routers.form_ga_config_router.get_supabase_client")
@patch("backend.services.form_ga_config_service.update_ga_configuration")
def test_update_ga_configuration_not_found(mock_update_config, mock_get_supabase, mock_auth, client):
    update_payload = {"description": "NonExistent Update"}
    mock_get_supabase.return_value = MagicMock()
    mock_update_config.return_value = None # Simulate not found by service

    response = client.put(f"{BASE_PATH}/{TEST_FORM_ID}", json=update_payload)

    assert response.status_code == 404

@patch("backend.routers.form_ga_config_router.get_current_active_user", return_value=MOCK_USER)
@patch("backend.routers.form_ga_config_router.get_supabase_client")
@patch("backend.services.form_ga_config_service.delete_ga_configuration")
def test_delete_ga_configuration_success(mock_delete_config, mock_get_supabase, mock_auth, client):
    mock_get_supabase.return_value = MagicMock()
    mock_delete_config.return_value = True # Simulate successful deletion

    response = client.delete(f"{BASE_PATH}/{TEST_FORM_ID}")

    assert response.status_code == 204

@patch("backend.routers.form_ga_config_router.get_current_active_user", return_value=MOCK_USER)
@patch("backend.routers.form_ga_config_router.get_supabase_client")
@patch("backend.services.form_ga_config_service.delete_ga_configuration")
def test_delete_ga_configuration_not_found(mock_delete_config, mock_get_supabase, mock_auth, client):
    mock_get_supabase.return_value = MagicMock()
    mock_delete_config.return_value = False # Simulate record not found or delete failed

    response = client.delete(f"{BASE_PATH}/{TEST_FORM_ID}")

    assert response.status_code == 404

# It's important that the patch paths like "backend.routers.form_ga_config_router.get_supabase_client"
# correctly point to where these names are looked up *within the context of the router file*.
# If get_supabase_client is imported as `from backend.db import get_supabase_client` in the router,
# then the patch path should be "backend.routers.form_ga_config_router.get_supabase_client" if that's how it's referenced,
# or "backend.db.get_supabase_client" if you want to patch it at its source (which affects all uses).
# Patching where it's *used* (in the router) is often more targeted for testing the router's logic.
# The current patching style uses decorators, which apply to the whole function.
# `client` is assumed to be a TestClient instance provided by pytest (e.g. via fixture or global).
