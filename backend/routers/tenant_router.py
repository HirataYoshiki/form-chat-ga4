# backend/routers/tenant_router.py
import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path # Added Path
from typing import List, Optional, Any
from supabase import Client

from backend.db import get_supabase_client
from backend.models.tenant_models import (
    TenantCreatePayload,
    TenantUpdatePayload,
    TenantResponse,
    TenantListResponse
)
from backend.services import tenant_service
from backend.auth import AuthenticatedUser, get_current_active_user # Import from auth.py

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/tenants",
    tags=["Tenant Management (Superuser Only)"] # Tag updated for clarity
)

# Dependency for superuser check
async def require_superuser_role(user: AuthenticatedUser = Depends(get_current_active_user)):
    # This assumes 'superuser' is a defined app_role for superusers.
    # And that user.tenant_id might be None for a superuser not tied to a specific tenant context by default.
    if user.app_role != "superuser":
        logger.warning(f"User {user.id} (role: {user.app_role}) attempted to access superuser-only tenant API at {router.prefix}.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to manage tenants."
        )
    return user

# Apply superuser check to all routes in this router
router.dependencies.append(Depends(require_superuser_role))


@router.post("", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant_endpoint(
    payload: TenantCreatePayload,
    supabase: Client = Depends(get_supabase_client)
    # superuser: AuthenticatedUser = Depends(require_superuser_role) # Covered by router dependency
):
    if supabase is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Supabase client unavailable")

    # Optional: Check if tenant with same company_name or domain already exists if they should be unique
    # This would require additional service methods like get_tenant_by_name/domain.
    # For now, relying on DB constraints if any (e.g. unique domain if schema had it).

    created_tenant_dict = await tenant_service.create_tenant(supabase, payload)
    if not created_tenant_dict:
        # Consider more specific error if service layer can provide it (e.g. duplicate)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create tenant. Check server logs for details.")
    return TenantResponse(**created_tenant_dict)


@router.get("", response_model=TenantListResponse)
async def list_tenants_endpoint(
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination."),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records to return."),
    show_deleted: bool = Query(False, description="Set to true to include logically deleted tenants."),
    supabase: Client = Depends(get_supabase_client)
):
    if supabase is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Supabase client unavailable")

    tenants_list_dict, total_count = await tenant_service.list_tenants(supabase, skip, limit, show_deleted)
    return TenantListResponse(
        tenants=[TenantResponse(**t) for t in tenants_list_dict],
        total_count=total_count,
        skip=skip,
        limit=limit
    )

@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant_endpoint(
    tenant_id: UUID = Path(..., description="The UUID of the tenant to retrieve."), # Use Path for path params
    supabase: Client = Depends(get_supabase_client)
):
    if supabase is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Supabase client unavailable")

    tenant_dict = await tenant_service.get_tenant(supabase, tenant_id)
    if not tenant_dict:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Tenant with id '{tenant_id}' not found.")
    return TenantResponse(**tenant_dict)

@router.put("/{tenant_id}", response_model=TenantResponse)
async def update_tenant_endpoint(
    tenant_id: UUID = Path(..., description="The UUID of the tenant to update."),
    payload: TenantUpdatePayload,
    supabase: Client = Depends(get_supabase_client)
):
    if supabase is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Supabase client unavailable")

    updated_tenant_dict = await tenant_service.update_tenant(supabase, tenant_id, payload)
    if not updated_tenant_dict:
        # This could be not found, or an empty update payload that resulted in no change (service returns current)
        # If service returns None specifically for "not found", then 404 is appropriate.
        # Assuming service returns None if tenant_id not found by update call.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Tenant with id '{tenant_id}' not found or update resulted in no change/failed.")
    return TenantResponse(**updated_tenant_dict)

@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant_endpoint(
    tenant_id: UUID = Path(..., description="The UUID of the tenant to delete."),
    hard_delete: bool = Query(False, description="Set to true to permanently (hard) delete the tenant. Default is logical delete."),
    supabase: Client = Depends(get_supabase_client)
):
    if supabase is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Supabase client unavailable")

    success = await tenant_service.delete_tenant(supabase, tenant_id, hard_delete)
    if not success:
        # Service's delete_tenant returns False if record not found (for hard delete)
        # or if already in the desired state (for logical delete, though service was updated to return True here).
        # Or if DB error occurs. For simplicity, map to 404 if not successful.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Tenant with id '{tenant_id}' not found or delete operation failed.")
    # For 204, FastAPI expects no return value (or None).
