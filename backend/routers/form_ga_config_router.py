# backend/routers/form_ga_config_router.py
from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import List, Optional, Any # Added Any for current_user
from supabase import Client

from backend.db import get_supabase_client
from backend.models.ga4_config_models import (
    GA4ConfigurationBase, # Changed from GA4ConfigurationCreatePayload
    GA4ConfigurationUpdatePayload,
    GA4ConfigurationResponse,
    GA4ConfigurationListResponse
)
from backend.services import form_ga_config_service
from backend.auth import AuthenticatedUser, get_current_active_user # Ensure AuthenticatedUser is imported

router = APIRouter(
    prefix="/api/v1/ga_configurations",
    tags=["GA4 Form Configurations"],
    dependencies=[Depends(get_current_active_user)]
)

@router.post("/{form_id}", response_model=GA4ConfigurationResponse, status_code=status.HTTP_201_CREATED)
async def create_ga_configuration_endpoint(
    form_id: str, # form_id from path
    payload: GA4ConfigurationBase, # Use base model for payload
    supabase: Client = Depends(get_supabase_client),
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    if supabase is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Supabase client unavailable")
    if not user.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User does not have a tenant ID.")

    existing_config = form_ga_config_service.get_ga_configuration(supabase, tenant_id=user.tenant_id, form_id=form_id)
    if existing_config:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"GA4 configuration for tenant '{user.tenant_id}', form_id '{form_id}' already exists."
        )

    created_config_dict = form_ga_config_service.create_ga_configuration(
        db=supabase,
        tenant_id=user.tenant_id,
        form_id=form_id,
        payload_base=payload
    )
    if not created_config_dict:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create GA4 configuration.")
    return GA4ConfigurationResponse(**created_config_dict)


@router.get("", response_model=GA4ConfigurationListResponse)
async def list_ga_configurations_endpoint(
    skip: int = 0,
    limit: int = 20,
    supabase: Client = Depends(get_supabase_client),
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    if supabase is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Supabase client unavailable")
    if not user.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User does not have a tenant ID.")

    configs_list_dict = form_ga_config_service.list_ga_configurations(
        db=supabase, tenant_id=user.tenant_id, skip=skip, limit=limit
    )
    # Ensure GA4ConfigurationResponse model can handle dicts from service (it should with from_attributes=True)
    response_items = [GA4ConfigurationResponse(**item) for item in configs_list_dict]
    return GA4ConfigurationListResponse(configurations=response_items)


@router.get("/{form_id}", response_model=GA4ConfigurationResponse)
async def get_ga_configuration_endpoint(
    form_id: str,
    supabase: Client = Depends(get_supabase_client),
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    if supabase is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Supabase client unavailable")
    if not user.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User does not have a tenant ID.")

    config_dict = form_ga_config_service.get_ga_configuration(supabase, tenant_id=user.tenant_id, form_id=form_id)
    if not config_dict:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"GA4 configuration for tenant '{user.tenant_id}', form_id '{form_id}' not found.")
    return GA4ConfigurationResponse(**config_dict)


@router.put("/{form_id}", response_model=GA4ConfigurationResponse)
async def update_ga_configuration_endpoint(
    form_id: str,
    payload: GA4ConfigurationUpdatePayload,
    supabase: Client = Depends(get_supabase_client),
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    if supabase is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Supabase client unavailable")
    if not user.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User does not have a tenant ID.")

    updated_config_dict = form_ga_config_service.update_ga_configuration(
        db=supabase, tenant_id=user.tenant_id, form_id=form_id, config_payload=payload
    )
    if not updated_config_dict:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"GA4 configuration for tenant '{user.tenant_id}', form_id '{form_id}' not found or no update performed.")
    return GA4ConfigurationResponse(**updated_config_dict)


@router.delete("/{form_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ga_configuration_endpoint(
    form_id: str,
    supabase: Client = Depends(get_supabase_client),
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    if supabase is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Supabase client unavailable")
    if not user.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User does not have a tenant ID.")

    success = form_ga_config_service.delete_ga_configuration(supabase, tenant_id=user.tenant_id, form_id=form_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"GA4 configuration for tenant '{user.tenant_id}', form_id '{form_id}' not found or delete failed.")
    # No body for 204 response
