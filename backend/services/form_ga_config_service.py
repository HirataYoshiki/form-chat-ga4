# backend/services/form_ga_config_service.py
import logging
from typing import List, Optional, Dict, Any
from supabase import Client
from backend.models.ga4_config_models import GA4ConfigurationCreatePayload, GA4ConfigurationUpdatePayload

logger = logging.getLogger(__name__)
TABLE_NAME = "form_ga_configurations"

def create_ga_configuration(
    db: Client,
    config_payload: GA4ConfigurationCreatePayload
) -> Optional[Dict[str, Any]]:
    """
    Creates a new GA4 configuration. form_id is part of config_payload.
    Returns the created record as a dictionary, or None if creation failed.
    """
    try:
        # Pydantic V2: .model_dump(), V1: .dict()
        data_to_insert = config_payload.model_dump()
        response = db.table(TABLE_NAME).insert(data_to_insert).execute()
        if response.data and len(response.data) > 0:
            logger.info(f"GA4 configuration created for form_id: {config_payload.form_id}")
            return response.data[0]
        else:
            logger.warning(
                f"Failed to create GA4 configuration for form_id: {config_payload.form_id}. "
                f"Supabase response: {response.model_dump_json() if hasattr(response, 'model_dump_json') else str(response)}"
            )
            return None
    except Exception as e: # More specific exceptions could be caught from supabase.exceptions
        logger.error(
            f"Exception creating GA4 configuration for form_id {config_payload.form_id}: {e}",
            exc_info=True
        )
        return None

def get_ga_configuration(db: Client, form_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves a GA4 configuration by form_id.
    Returns the record as a dictionary, or None if not found.
    """
    try:
        response = db.table(TABLE_NAME).select("*").eq("form_id", form_id).single().execute() # Use single() for one record
        # single() returns the object directly in .data if found, or raises an error if >1, or data is None if 0
        if response.data:
            return response.data
        else: # Should be caught by PostgrestAPIError if not found with single(), but defensive check
            return None
    except Exception as e: # Catch supabase.exceptions.PostgrestAPIError for "No rows found" specifically if desired
        logger.error(f"Exception retrieving GA4 configuration for form_id {form_id}: {e}", exc_info=True)
        return None

def list_ga_configurations(db: Client, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Lists GA4 configurations with pagination.
    Returns a list of records (dictionaries).
    """
    try:
        # Supabase range is 'from' (inclusive) and 'to' (inclusive).
        # So, if skip=0, limit=10, range is 0 to 9.
        response = db.table(TABLE_NAME).select("*").range(skip, skip + limit - 1).execute()
        return response.data if response.data else []
    except Exception as e:
        logger.error(f"Exception listing GA4 configurations: {e}", exc_info=True)
        return []

def update_ga_configuration(
    db: Client,
    form_id: str,
    config_payload: GA4ConfigurationUpdatePayload
) -> Optional[Dict[str, Any]]:
    """
    Updates an existing GA4 configuration for a given form_id.
    Only updates fields present in the payload (non-None).
    Returns the updated record as a dictionary, or None if not found or update failed.
    """
    try:
        # Pydantic V2: .model_dump(exclude_unset=True) to get only provided fields
        data_to_update = config_payload.model_dump(exclude_unset=True)

        if not data_to_update:
            logger.info(f"No fields to update for GA4 configuration form_id: {form_id}. Returning current record.")
            return get_ga_configuration(db, form_id) # Return existing if no update data

        response = db.table(TABLE_NAME).update(data_to_update).eq("form_id", form_id).execute()
        if response.data and len(response.data) > 0:
            logger.info(f"GA4 configuration updated for form_id: {form_id}")
            return response.data[0]
        else: # Record not found or RLS prevented update
            logger.warning(
                f"Failed to update GA4 configuration for form_id: {form_id} (it may not exist or no data returned). "
                f"Supabase response: {response.model_dump_json() if hasattr(response, 'model_dump_json') else str(response)}"
            )
            return None
    except Exception as e:
        logger.error(f"Exception updating GA4 configuration for form_id {form_id}: {e}", exc_info=True)
        return None

def delete_ga_configuration(db: Client, form_id: str) -> bool:
    """
    Deletes a GA4 configuration by form_id.
    Returns True if deletion was successful (record existed and was deleted), False otherwise.
    """
    try:
        response = db.table(TABLE_NAME).delete().eq("form_id", form_id).execute()
        # Check if data was returned (Supabase often returns the deleted record(s))
        # and if the count of returned data is greater than 0.
        if response.data and len(response.data) > 0:
            logger.info(f"GA4 configuration deleted for form_id: {form_id}")
            return True
        else:
            # This could mean the record didn't exist, or delete simply returned no data.
            # If record not existing is not an error, this is fine.
            # If it should be an error if record doesn't exist, then a prior GET might be needed.
            logger.warning(f"GA4 configuration for form_id: {form_id} not found or delete returned no data. Response: {response.model_dump_json() if hasattr(response, 'model_dump_json') else str(response)}")
            return False # Or True if "not found" is also considered success for a delete op
    except Exception as e:
        logger.error(f"Exception deleting GA4 configuration for form_id {form_id}: {e}", exc_info=True)
        return False
