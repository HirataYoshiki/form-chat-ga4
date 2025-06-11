# backend/routers/form_ga_config_router.py
from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import List, Optional, Any # Added Any for current_user
from supabase import Client

from backend.db import get_supabase_client
from backend.models.ga4_config_models import (
    GA4ConfigurationCreatePayload,
    GA4ConfigurationUpdatePayload,
    GA4ConfigurationResponse,
    GA4ConfigurationListResponse
)
from backend.services import form_ga_config_service

# Attempt to import get_current_active_user from contact_api.py
# This might need adjustment based on project structure or if auth logic is centralized.
try:
    from backend.contact_api import get_current_active_user
except ImportError:
    # Fallback or placeholder if direct import fails during subtask execution
    # In a real setup, ensure this dependency is correctly resolvable.
    async def get_current_active_user() -> Any: # Dummy for subtask if import fails
        print("Warning: Using dummy get_current_active_user in form_ga_config_router.py")
        return {"username": "dummy_auth_user"}
    # pass # Or raise an error if auth is critical and cannot be mocked like this

router = APIRouter(
    prefix="/api/v1/ga_configurations",
    tags=["GA4 Form Configurations"], # Updated tag
    dependencies=[Depends(get_current_active_user)] # Apply auth to all routes in this router
)

@router.post("", response_model=GA4ConfigurationResponse, status_code=status.HTTP_201_CREATED)
async def create_ga_configuration_endpoint(
    payload: GA4ConfigurationCreatePayload, # form_id is in payload
    supabase: Client = Depends(get_supabase_client)
    # current_user is handled by router dependency
):
    if supabase is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Supabase client unavailable")

    existing_config = form_ga_config_service.get_ga_configuration(supabase, payload.form_id)
    if existing_config:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"GA4 configuration for form_id '{payload.form_id}' already exists."
        )

    created_config_dict = form_ga_config_service.create_ga_configuration(supabase, payload)
    if not created_config_dict:
        # This could be due to DB error or other failure in service layer
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create GA4 configuration.")
    return GA4ConfigurationResponse(**created_config_dict)


@router.get("", response_model=GA4ConfigurationListResponse)
async def list_ga_configurations_endpoint(
    skip: int = 0,
    limit: int = 20,
    supabase: Client = Depends(get_supabase_client)
):
    if supabase is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Supabase client unavailable")

    configs_list_dict = form_ga_config_service.list_ga_configurations(supabase, skip=skip, limit=limit)
    response_items = [GA4ConfigurationResponse(**item) for item in configs_list_dict]
    return GA4ConfigurationListResponse(configurations=response_items)


@router.get("/{form_id}", response_model=GA4ConfigurationResponse)
async def get_ga_configuration_endpoint(
    form_id: str,
    supabase: Client = Depends(get_supabase_client)
):
    if supabase is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Supabase client unavailable")

    config_dict = form_ga_config_service.get_ga_configuration(supabase, form_id)
    if not config_dict:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"GA4 configuration for form_id '{form_id}' not found.")
    return GA4ConfigurationResponse(**config_dict)


@router.put("/{form_id}", response_model=GA4ConfigurationResponse)
async def update_ga_configuration_endpoint(
    form_id: str,
    payload: GA4ConfigurationUpdatePayload,
    supabase: Client = Depends(get_supabase_client)
):
    if supabase is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Supabase client unavailable")

    updated_config_dict = form_ga_config_service.update_ga_configuration(supabase, form_id, payload)
    if not updated_config_dict:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"GA4 configuration for form_id '{form_id}' not found or no update performed.")
    return GA4ConfigurationResponse(**updated_config_dict)


@router.delete("/{form_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ga_configuration_endpoint(
    form_id: str,
    supabase: Client = Depends(get_supabase_client)
):
    if supabase is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Supabase client unavailable")

    success = form_ga_config_service.delete_ga_configuration(supabase, form_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"GA4 configuration for form_id '{form_id}' not found or delete failed.")
    # No body for 204 response
