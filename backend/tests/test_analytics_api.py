import pytest
from fastapi import HTTPException # For potential auth mock
from fastapi.testclient import TestClient
from datetime import date, datetime
from typing import List, Dict, Any, Optional

# Attempt to import from the project structure.
# These paths assume the test runner is configured to find the 'backend' module.
try:
    from backend.contact_api import app, get_db, get_current_active_user # Import dependencies to override
    from backend.models.analytics_models import SubmissionsCountParams
    from backend.services import analytics_service # To use mocker.patch effectively
except ImportError:
    # Fallback for environments where the above might not resolve directly
    # (e.g., simplified subtask execution). This is not for production.
    from contact_api import app, get_db, get_current_active_user # type: ignore
    from models.analytics_models import SubmissionsCountParams # type: ignore
    import services.analytics_service as analytics_service # type: ignore


client = TestClient(app)

# --- Mock Dependencies ---

async def override_get_db_success_mock():
    # This mock should yield something that your service layer can nominally work with,
    # or your service layer calls should also be mocked.
    # If service layer is mocked (as done in these tests), this can be simple.
    yield {"db_type": "mock_success_session"}

async def override_get_db_unavailable_mock():
    # This simulates the scenario where get_db in contact_api.py yields None
    yield None

async def override_get_current_active_user_success_mock():
    return {"username": "testuser", "permissions": ["view_analytics"]}

# This mock simulates an authentication failure by raising HTTPException
# This is how a real auth dependency would signal an issue.
async def override_get_current_active_user_raises_401_mock():
    raise HTTPException(status_code=401, detail="Not authenticated for test")


# --- Test Cases ---

@pytest.fixture(autouse=True)
def cleanup_dependency_overrides():
    # This fixture runs before each test and cleans up overrides after each test.
    original_get_db = app.dependency_overrides.get(get_db)
    original_get_user = app.dependency_overrides.get(get_current_active_user)
    yield
    # Restore original overrides or clear them
    if original_get_db:
        app.dependency_overrides[get_db] = original_get_db
    else:
        if get_db in app.dependency_overrides:
            del app.dependency_overrides[get_db]
    if original_get_user:
        app.dependency_overrides[get_current_active_user] = original_get_user
    else:
        if get_current_active_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_active_user]


def test_get_submissions_count_success_no_params(mocker):
    mock_service_call = mocker.patch.object(analytics_service, "get_submissions_count", return_value=123)
    app.dependency_overrides[get_db] = override_get_db_success_mock
    app.dependency_overrides[get_current_active_user] = override_get_current_active_user_success_mock

    response = client.get("/api/v1/analytics/submissions/count")

    assert response.status_code == 200
    expected_params_dict = SubmissionsCountParams(start_date=None, end_date=None, form_id=None).dict()
    assert response.json() == {"count": 123, "parameters": expected_params_dict}
    mock_service_call.assert_called_once_with(db=mocker.ANY, start_date=None, end_date=None, form_id=None)

def test_get_submissions_count_success_with_params(mocker):
    mock_service_call = mocker.patch.object(analytics_service, "get_submissions_count", return_value=42)
    app.dependency_overrides[get_db] = override_get_db_success_mock
    app.dependency_overrides[get_current_active_user] = override_get_current_active_user_success_mock

    start_str, end_str, form_val = "2023-01-01", "2023-01-31", "test_form"

    response = client.get(
        f"/api/v1/analytics/submissions/count?start_date={start_str}&end_date={end_str}&form_id={form_val}"
    )

    assert response.status_code == 200
    resp_json = response.json()
    assert resp_json["count"] == 42
    assert resp_json["parameters"]["start_date"] == start_str
    assert resp_json["parameters"]["end_date"] == end_str
    assert resp_json["parameters"]["form_id"] == form_val
    mock_service_call.assert_called_once_with(
        db=mocker.ANY, start_date=date(2023,1,1), end_date=date(2023,1,31), form_id=form_val
    )

def test_get_submissions_count_auth_failure(mocker):
    # This test now uses an override that raises HTTPException for auth.
    app.dependency_overrides[get_db] = override_get_db_success_mock # DB is fine
    app.dependency_overrides[get_current_active_user] = override_get_current_active_user_raises_401_mock

    response = client.get("/api/v1/analytics/submissions/count")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated for test"}

def test_get_submissions_count_db_unavailable(mocker):
    app.dependency_overrides[get_db] = override_get_db_unavailable_mock # get_db yields None
    app.dependency_overrides[get_current_active_user] = override_get_current_active_user_success_mock

    response = client.get("/api/v1/analytics/submissions/count")
    assert response.status_code == 503
    assert response.json() == {"detail": "Database service not configured or unavailable."}


def test_get_summary_by_form_success(mocker):
    expected_summary = [{"form_id": "form_A", "count": 78}, {"form_id": "form_B", "count": 45}]
    mock_service_call = mocker.patch.object(analytics_service, "get_summary_by_form", return_value=expected_summary)
    app.dependency_overrides[get_db] = override_get_db_success_mock
    app.dependency_overrides[get_current_active_user] = override_get_current_active_user_success_mock

    response = client.get("/api/v1/analytics/submissions/summary_by_form")

    assert response.status_code == 200
    assert response.json() == {"summary": expected_summary}
    mock_service_call.assert_called_once_with(db=mocker.ANY)

def test_get_summary_by_form_auth_failure(mocker):
    app.dependency_overrides[get_db] = override_get_db_success_mock
    app.dependency_overrides[get_current_active_user] = override_get_current_active_user_raises_401_mock

    response = client.get("/api/v1/analytics/submissions/summary_by_form")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated for test"}


def test_get_summary_by_form_db_unavailable(mocker):
    app.dependency_overrides[get_db] = override_get_db_unavailable_mock
    app.dependency_overrides[get_current_active_user] = override_get_current_active_user_success_mock

    response = client.get("/api/v1/analytics/submissions/summary_by_form")
    assert response.status_code == 503
    assert response.json() == {"detail": "Database service not configured or unavailable."}
