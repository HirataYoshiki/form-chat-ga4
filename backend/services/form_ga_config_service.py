# backend/services/form_ga_config_service.py
import logging
from typing import List, Optional, Dict, Any
from supabase import Client
# GA4ConfigurationCreatePayload is now GA4ConfigurationBase for the service create function
from backend.models.ga4_config_models import GA4ConfigurationBase, GA4ConfigurationUpdatePayload

logger = logging.getLogger(__name__)
TABLE_NAME = "form_ga_configurations"

def create_ga_configuration(
    db: Client,
    tenant_id: str,
    form_id: str,
    payload_base: GA4ConfigurationBase
) -> Optional[Dict[str, Any]]:
    """
    Creates a new GA4 configuration for a specific tenant and form_id.
    Returns the created record as a dictionary, or None if creation failed.
    """
    try:
        data_to_insert = payload_base.model_dump()
        data_to_insert["tenant_id"] = tenant_id
        data_to_insert["form_id"] = form_id

        response = db.table(TABLE_NAME).insert(data_to_insert).execute()
        if response.data and len(response.data) > 0:
            logger.info(f"GA4 configuration created for tenant_id: {tenant_id}, form_id: {form_id}")
            return response.data[0]
        else:
            logger.warning(
                f"Failed to create GA4 configuration for tenant_id: {tenant_id}, form_id: {form_id}. "
                f"Supabase response: {response.model_dump_json() if hasattr(response, 'model_dump_json') else str(response)}"
            )
            return None
    except Exception as e: # More specific exceptions could be caught from supabase.exceptions
        logger.error(
            f"Exception creating GA4 configuration for tenant_id: {tenant_id}, form_id {form_id}: {e}",
            exc_info=True
        )
        return None

def get_ga_configuration(db: Client, tenant_id: str, form_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves a GA4 configuration by tenant_id and form_id.
    Returns the record as a dictionary, or None if not found.
    """
    try:
        response = (
            db.table(TABLE_NAME)
            .select("*")
            .eq("tenant_id", tenant_id) # Added tenant_id filter
            .eq("form_id", form_id)
            .single()
            .execute()
        )
        # single() returns the object directly in .data if found, or raises an error if >1, or data is None if 0
        if response.data:
            return response.data
        else: # Should be caught by PostgrestAPIError if not found with single(), but defensive check
            logger.info(f"No GA4 configuration found for tenant_id '{tenant_id}' and form_id '{form_id}'.")
            return None
    except Exception as e: # Catch supabase.exceptions.PostgrestAPIError for "No rows found" specifically if desired
        logger.error(f"Exception retrieving GA4 configuration for tenant_id '{tenant_id}', form_id '{form_id}': {e}", exc_info=True)
        return None

def list_ga_configurations(db: Client, tenant_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Lists GA4 configurations for a specific tenant with pagination.
    Returns a list of records (dictionaries).
    """
    try:
        response = (
            db.table(TABLE_NAME)
            .select("*")
            .eq("tenant_id", tenant_id)
            .range(skip, skip + limit - 1)
            .execute()
        )
        return response.data if response.data else []
    except Exception as e:
        logger.error(f"Exception listing GA4 configurations for tenant_id {tenant_id}: {e}", exc_info=True)
        return []

def update_ga_configuration(
    db: Client,
    tenant_id: str,
    form_id: str,
    config_payload: GA4ConfigurationUpdatePayload
) -> Optional[Dict[str, Any]]:
    """
    Updates an existing GA4 configuration for a given tenant_id and form_id.
    Only updates fields present in the payload (non-None).
    Returns the updated record as a dictionary, or None if not found or update failed.
    """
    try:
        data_to_update = config_payload.model_dump(exclude_unset=True)

        if not data_to_update:
            logger.info(f"No fields to update for GA4 configuration for tenant_id: {tenant_id}, form_id: {form_id}. Returning current record.")
            return get_ga_configuration(db, tenant_id, form_id)

        response = (
            db.table(TABLE_NAME)
            .update(data_to_update)
            .eq("tenant_id", tenant_id)
            .eq("form_id", form_id)
            .execute()
        )
        if response.data and len(response.data) > 0:
            logger.info(f"GA4 configuration updated for tenant_id: {tenant_id}, form_id: {form_id}")
            return response.data[0]
        else:
            logger.warning(
                f"Failed to update GA4 configuration for tenant_id: {tenant_id}, form_id: {form_id} (it may not exist or no data returned). "
                f"Supabase response: {response.model_dump_json() if hasattr(response, 'model_dump_json') else str(response)}"
            )
            return None
    except Exception as e:
        logger.error(f"Exception updating GA4 configuration for tenant_id: {tenant_id}, form_id {form_id}: {e}", exc_info=True)
        return None

def delete_ga_configuration(db: Client, tenant_id: str, form_id: str) -> bool:
    """
    Deletes a GA4 configuration by tenant_id and form_id.
    Returns True if deletion was successful, False otherwise.
    """
    try:
        response = (
            db.table(TABLE_NAME)
            .delete()
            .eq("tenant_id", tenant_id)
            .eq("form_id", form_id)
            .execute()
        )
        if response.data and len(response.data) > 0:
            logger.info(f"GA4 configuration deleted for tenant_id: {tenant_id}, form_id: {form_id}")
            return True
        else:
            logger.warning(f"GA4 configuration for tenant_id: {tenant_id}, form_id: {form_id} not found or delete returned no data. Response: {response.model_dump_json() if hasattr(response, 'model_dump_json') else str(response)}")
            return False
    except Exception as e:
        logger.error(f"Exception deleting GA4 configuration for tenant_id: {tenant_id}, form_id {form_id}: {e}", exc_info=True)
        return False
