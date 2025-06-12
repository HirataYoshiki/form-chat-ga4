# backend/models/tenant_models.py
from pydantic import BaseModel, Field, UUID4, ConfigDict
from typing import Optional, List
from datetime import datetime

class TenantBase(BaseModel):
    company_name: str = Field(..., min_length=1, description="Name of the tenant company.")
    domain: Optional[str] = Field(
        None,
        description="Domain associated with the tenant (e.g., company website). Can be null.",
        examples=["example.com"]
    )

class TenantCreatePayload(TenantBase):
    """Payload for creating a new tenant."""
    pass

class TenantUpdatePayload(BaseModel):
    """Payload for updating an existing tenant. All fields are optional."""
    company_name: Optional[str] = Field(None, min_length=1, description="New company name, if changing.")
    domain: Optional[str] = Field(None, description="New domain, if changing. Set to null to clear.")
    is_deleted: Optional[bool] = Field(None, description="Set to true to logically delete, false to restore.")

class TenantResponse(TenantBase):
    """Response model for a tenant, including database-generated fields."""
    tenant_id: UUID4 # UUID type from Pydantic
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True) # For Pydantic V2 ORM mode

class TenantListResponse(BaseModel):
    """Response model for listing tenants with pagination info."""
    tenants: List[TenantResponse]
    total_count: int = Field(..., description="Total number of tenants matching filter criteria.")
    skip: int = Field(..., ge=0, description="Number of records skipped (offset).")
    limit: int = Field(..., ge=1, description="Maximum number of records returned.")
