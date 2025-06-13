import functions_framework
from google.cloud import aiplatform_v1beta1 as aiplatform
from google.api_core import operation as ga_operation # For LRO details
from supabase import create_client, Client
import os
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize clients
try:
    # Re-using settings and client getters from the main backend application if possible
    # This is a simplified client initialization for the Cloud Function context.
    # For actual deployment, package structure or shared modules would be needed.
    from backend.config import settings
    from backend.services.vertex_ai_client import get_rag_data_service_client
except ImportError:
    logger_import_fallback = logging.getLogger(__name__)
    logger_import_fallback.warning(
        "Failed to import from 'backend' package. Using mock settings and client for RAG LRO Monitor CF. "
        "Ensure 'backend' module is in PYTHONPATH or packaged for deployment."
    )
    class MockSettings: # Fallback if backend package not available
        PROJECT_ID = os.environ.get("PROJECT_ID")
        VERTEX_AI_REGION = os.environ.get("VERTEX_AI_REGION", "us-central1")
    settings = MockSettings()

    def get_rag_data_service_client(project_id=None, location=None): # Fallback
        p_id = project_id or settings.PROJECT_ID
        loc = location or settings.VERTEX_AI_REGION
        if not p_id or not loc:
            logger_import_fallback.error("Mock get_rag_data_service_client: PROJECT_ID or VERTEX_AI_REGION not set.")
            raise ValueError("PROJECT_ID or VERTEX_AI_REGION not set for mock Vertex AI client.")
        client_options = {"api_endpoint": f"{loc}-aiplatform.googleapis.com"}
        return aiplatform.VertexRagDataServiceClient(client_options=client_options)


SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase_client: Client = None
if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
    try:
        supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
else:
    logger.warning("Supabase URL or Service Role Key not configured for RAG LRO Monitor.")


@functions_framework.http
def monitor_rag_import_operations(request):
    """
    Periodically checks the status of ongoing Vertex AI RAG import operations
    and updates their status in the database.
    """
    if not supabase_client:
        logger.error("Supabase client not initialized. Cannot proceed.")
        return ("Internal Server Error: DB client not configured", 500)
    if not settings.PROJECT_ID or not settings.VERTEX_AI_REGION:
        logger.error("Project ID or Vertex AI Region not configured.")
        return ("Internal Server Error: Project/Region not configured", 500)

    logger.info("Starting RAG import LRO monitoring run.")

    try:
        # 1. Fetch records from rag_uploaded_files with status 'importing'
        response = supabase_client.table("rag_uploaded_files").select("processing_id, vertex_ai_operation_name, tenant_id").eq("processing_status", "importing").execute()

        if response.data:
            logger.info(f"Found {len(response.data)} operations to monitor.")
            aiplatform_client = get_rag_data_service_client()

            for record in response.data:
                processing_id = record.get("processing_id")
                operation_name = record.get("vertex_ai_operation_name")
                tenant_id = record.get("tenant_id")

                if not operation_name:
                    logger.warning(f"Skipping record {processing_id} for tenant {tenant_id} due to missing operation name.")
                    continue

                logger.info(f"Checking status for operation: {operation_name} (processing_id: {processing_id})")

                try:
                    op = aiplatform_client.operations_client.get_operation(name=operation_name)

                    if op.done:
                        if op.error.code != 0:
                            error_message = f"Operation failed: {op.error.message} (Code: {op.error.code})"
                            logger.error(f"Operation {operation_name} for {processing_id} failed: {error_message}")
                            supabase_client.table("rag_uploaded_files").update({
                                "processing_status": "failed",
                                "status_message": error_message
                            }).eq("processing_id", processing_id).execute()
                        else:
                            logger.info(f"Operation {operation_name} for {processing_id} completed successfully.")
                            status_update = {
                                "processing_status": "completed",
                                "status_message": "Import to Vertex AI RAG completed successfully."
                            }
                            supabase_client.table("rag_uploaded_files").update(status_update).eq("processing_id", processing_id).execute()
                    else:
                        logger.info(f"Operation {operation_name} for {processing_id} is still running.")
                except Exception as e:
                    logger.error(f"Error checking LRO {operation_name} for {processing_id}: {e}", exc_info=True)
        else:
            logger.info("No RAG import operations currently in 'importing' state.")

        return ("RAG LRO monitoring run completed.", 200)

    except Exception as e:
        logger.error(f"Unhandled error in RAG LRO monitor: {e}", exc_info=True)
        return ("Internal Server Error during RAG LRO monitoring.", 500)
