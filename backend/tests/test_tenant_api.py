# backend/tests/test_tenant_api.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch, ANY as AnyMockValue
from uuid import uuid4, UUID # Import UUID for type checks
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

try:
    from backend.contact_api import app
    from backend.auth import AuthenticatedUser # For mocking user
except ImportError:
    from contact_api import app # type: ignore
    # Define dummy AuthenticatedUser if needed for subtask environment
    class AuthenticatedUser:
        def __init__(self, id: str, app_role: str, tenant_id: Optional[str] = None, email: Optional[str] = None, full_name: Optional[str] = None):
            self.id = id
            self.app_role = app_role
            self.tenant_id = tenant_id
            self.email = email
            self.full_name = full_name


client = TestClient(app)

# --- Mock Data & Helpers ---
TENANTS_API_BASE_PATH = "/api/v1/tenants"
MOCK_SUPERUSER = AuthenticatedUser(id="super-user-id", app_role="superuser", tenant_id=None)
MOCK_NON_SUPERUSER = AuthenticatedUser(id="normal-user-id", app_role="user", tenant_id=str(uuid4()))

def helper_mock_tenant_payload_dict(company_name: str = "Test Tenant Inc.", domain: Optional[str] = "test-tenant.com") -> Dict[str, Any]:
    return {"company_name": company_name, "domain": domain}

def helper_mock_tenant_db_record_dict(
    tenant_id: Optional[UUID] = None, # Allow passing None for creation where DB generates it
    company_name: str = "Test Tenant Inc.",
    domain: Optional[str] = "test-tenant.com",
    is_deleted: bool = False
) -> Dict[str, Any]:
    return {
        "tenant_id": str(tenant_id if tenant_id else uuid4()), # Convert UUID to str for JSON comparison
        "company_name": company_name,
        "domain": domain,
        "is_deleted": is_deleted,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

# --- Test Cases ---

# CREATE Tenant
@patch("backend.routers.tenant_router.get_current_active_user", return_value=MOCK_SUPERUSER)
@patch("backend.routers.tenant_router.get_supabase_client")
@patch("backend.services.tenant_service.create_tenant")
def test_create_tenant_success_as_superuser(mock_create_svc, mock_get_supabase, mock_auth, client):
    payload = helper_mock_tenant_payload_dict()
    mock_supabase_instance = MagicMock()
    mock_get_supabase.return_value = mock_supabase_instance

    # create_tenant service returns a dict representing the DB record
    db_record = helper_mock_tenant_db_record_dict(**payload) # Pass payload fields
    mock_create_svc.return_value = db_record

    response = client.post(TENANTS_API_BASE_PATH, json=payload)

    assert response.status_code == 201
    resp_data = response.json()
    assert resp_data["company_name"] == payload["company_name"]
    assert resp_data["domain"] == payload["domain"]
    assert resp_data["is_deleted"] is False # Default
    assert "tenant_id" in resp_data
    mock_create_svc.assert_called_once()
    # Check payload passed to service (Pydantic model in service, dict here is fine if fields match)
    # The service receives TenantCreatePayload, so its .model_dump() would be passed.
    # For simplicity, checking if called is often enough if payload structure is simple.

@patch("backend.routers.tenant_router.get_current_active_user", return_value=MOCK_NON_SUPERUSER)
def test_create_tenant_fail_as_non_superuser(mock_auth, client):
    payload = helper_mock_tenant_payload_dict()
    response = client.post(TENANTS_API_BASE_PATH, json=payload)
    assert response.status_code == 403

# GET Tenant List
@patch("backend.routers.tenant_router.get_current_active_user", return_value=MOCK_SUPERUSER)
@patch("backend.routers.tenant_router.get_supabase_client")
@patch("backend.services.tenant_service.list_tenants")
def test_list_tenants_success_as_superuser(mock_list_svc, mock_get_supabase, mock_auth, client):
    mock_supabase_instance = MagicMock()
    mock_get_supabase.return_value = mock_supabase_instance

    mock_tenants_data = [
        helper_mock_tenant_db_record_dict(company_name="Tenant A"),
        helper_mock_tenant_db_record_dict(company_name="Tenant B", is_deleted=True)
    ]
    mock_total = 2
    mock_list_svc.return_value = (mock_tenants_data, mock_total)

    response = client.get(TENANTS_API_BASE_PATH, params={"show_deleted": True, "skip": 0, "limit": 10})

    assert response.status_code == 200
    resp_data = response.json()
    assert len(resp_data["tenants"]) == 2
    assert resp_data["total_count"] == mock_total
    assert resp_data["tenants"][0]["company_name"] == "Tenant A"
    mock_list_svc.assert_called_once_with(mock_supabase_instance, 0, 10, True)

# GET Single Tenant
@patch("backend.routers.tenant_router.get_current_active_user", return_value=MOCK_SUPERUSER)
@patch("backend.routers.tenant_router.get_supabase_client")
@patch("backend.services.tenant_service.get_tenant")
def test_get_tenant_success_as_superuser(mock_get_svc, mock_get_supabase, mock_auth, client):
    tenant_id = uuid4()
    db_record = helper_mock_tenant_db_record_dict(tenant_id=tenant_id)
    mock_supabase_instance = MagicMock()
    mock_get_supabase.return_value = mock_supabase_instance
    mock_get_svc.return_value = db_record

    response = client.get(f"{TENANTS_API_BASE_PATH}/{str(tenant_id)}")
    assert response.status_code == 200
    assert response.json()["tenant_id"] == str(tenant_id)
    mock_get_svc.assert_called_once_with(mock_supabase_instance, tenant_id)

@patch("backend.routers.tenant_router.get_current_active_user", return_value=MOCK_SUPERUSER)
@patch("backend.routers.tenant_router.get_supabase_client")
@patch("backend.services.tenant_service.get_tenant")
def test_get_tenant_not_found_as_superuser(mock_get_svc, mock_get_supabase, mock_auth, client):
    tenant_id = uuid4()
    mock_supabase_instance = MagicMock()
    mock_get_supabase.return_value = mock_supabase_instance
    mock_get_svc.return_value = None # Simulate not found

    response = client.get(f"{TENANTS_API_BASE_PATH}/{str(tenant_id)}")
    assert response.status_code == 404

# UPDATE Tenant
@patch("backend.routers.tenant_router.get_current_active_user", return_value=MOCK_SUPERUSER)
@patch("backend.routers.tenant_router.get_supabase_client")
@patch("backend.services.tenant_service.update_tenant")
def test_update_tenant_success_as_superuser(mock_update_svc, mock_get_supabase, mock_auth, client):
    tenant_id = uuid4()
    update_payload = {"company_name": "Updated Tenant Name", "is_deleted": True}

    # Simulate what the service would return after update
    updated_db_record = helper_mock_tenant_db_record_dict(
        tenant_id=tenant_id,
        company_name="Updated Tenant Name",
        is_deleted=True
    )
    mock_supabase_instance = MagicMock()
    mock_get_supabase.return_value = mock_supabase_instance
    mock_update_svc.return_value = updated_db_record

    response = client.put(f"{TENANTS_API_BASE_PATH}/{str(tenant_id)}", json=update_payload)
    assert response.status_code == 200
    resp_data = response.json()
    assert resp_data["company_name"] == "Updated Tenant Name"
    assert resp_data["is_deleted"] is True
    # Check that service was called with Pydantic model (or its dict representation)
    # The router passes TenantUpdatePayload to the service.
    mock_update_svc.assert_called_once()
    # More specific check on payload if needed:
    # from backend.models.tenant_models import TenantUpdatePayload
    # expected_service_payload = TenantUpdatePayload(**update_payload)
    # mock_update_svc.assert_called_once_with(mock_supabase_instance, tenant_id, expected_service_payload)


# DELETE Tenant (Logical)
@patch("backend.routers.tenant_router.get_current_active_user", return_value=MOCK_SUPERUSER)
@patch("backend.routers.tenant_router.get_supabase_client")
@patch("backend.services.tenant_service.delete_tenant")
def test_delete_tenant_logical_success_as_superuser(mock_delete_svc, mock_get_supabase, mock_auth, client):
    tenant_id = uuid4()
    mock_supabase_instance = MagicMock()
    mock_get_supabase.return_value = mock_supabase_instance
    mock_delete_svc.return_value = True # Simulate successful logical delete

    response = client.delete(f"{TENANTS_API_BASE_PATH}/{str(tenant_id)}", params={"hard_delete": False})
    assert response.status_code == 204
    mock_delete_svc.assert_called_once_with(mock_supabase_instance, tenant_id, False)

# DELETE Tenant (Hard)
@patch("backend.routers.tenant_router.get_current_active_user", return_value=MOCK_SUPERUSER)
@patch("backend.routers.tenant_router.get_supabase_client")
@patch("backend.services.tenant_service.delete_tenant")
def test_delete_tenant_hard_success_as_superuser(mock_delete_svc, mock_get_supabase, mock_auth, client):
    tenant_id = uuid4()
    mock_supabase_instance = MagicMock()
    mock_get_supabase.return_value = mock_supabase_instance
    mock_delete_svc.return_value = True

    response = client.delete(f"{TENANTS_API_BASE_PATH}/{str(tenant_id)}", params={"hard_delete": True})
    assert response.status_code == 204
    mock_delete_svc.assert_called_once_with(mock_supabase_instance, tenant_id, True)

@patch("backend.routers.tenant_router.get_current_active_user", return_value=MOCK_SUPERUSER)
@patch("backend.routers.tenant_router.get_supabase_client")
@patch("backend.services.tenant_service.delete_tenant")
def test_delete_tenant_not_found_as_superuser(mock_delete_svc, mock_get_supabase, mock_auth, client):
    tenant_id = uuid4()
    mock_supabase_instance = MagicMock()
    mock_get_supabase.return_value = mock_supabase_instance
    mock_delete_svc.return_value = False # Simulate tenant not found by service

    response = client.delete(f"{TENANTS_API_BASE_PATH}/{str(tenant_id)}")
    assert response.status_code == 404
