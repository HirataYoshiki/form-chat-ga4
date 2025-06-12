# backend/models/ga4_config_models.py
from pydantic import BaseModel, Field, ConfigDict # ConfigDict for Pydantic V2
from typing import Optional, List
from datetime import datetime

class GA4ConfigurationBase(BaseModel):
    ga4_measurement_id: str = Field(
        ...,
        min_length=1,
        description="GA4 Measurement ID (e.g., G-XXXXXXXXXX).",
        examples=["G-1234567890"]
    )
    ga4_api_secret: str = Field(
        ...,
        min_length=1,
        description="GA4 API Secret for Measurement Protocol. This is sensitive data."
    )
    description: Optional[str] = Field(
        None,
        description="Optional human-readable description for this GA4 configuration set.",
        examples=["Main contact form GA4 settings"]
    )

class GA4ConfigurationCreatePayload(GA4ConfigurationBase):
    """
    Payload for creating a new GA4 configuration.
    form_id will be a path parameter, tenant_id from authenticated user.
    """
    pass # Inherits all fields from GA4ConfigurationBase, form_id removed

class GA4ConfigurationUpdatePayload(BaseModel):
    """
    Payload for updating an existing GA4 configuration.
    All fields are optional; only provided fields will be updated.
    """
    ga4_measurement_id: Optional[str] = Field(
        None,
        min_length=1,
        description="New GA4 Measurement ID, if changing."
    )
    ga4_api_secret: Optional[str] = Field(
        None,
        min_length=1,
        description="New GA4 API Secret, if changing. This is sensitive data."
    )
    description: Optional[str] = Field(
        None,
        description="New or updated description for this GA4 configuration set."
    )

class GA4ConfigurationResponse(GA4ConfigurationBase):
    """
    Represents a GA4 configuration record as returned by the API.
    Includes database-generated fields like tenant_id, form_id, created_at, and updated_at.
    """
    tenant_id: str # Added
    form_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GA4ConfigurationListResponse(BaseModel):
    """
    Response model for listing multiple GA4 configurations.
    """
    configurations: List[GA4ConfigurationResponse]
