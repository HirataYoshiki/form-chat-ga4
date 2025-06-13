import functions_framework
from google.cloud import aiplatform_v1beta1 as aiplatform
from supabase import create_client, Client
import os
import json
import logging
import uuid

# Import settings and Vertex AI client utilities from the main backend application
# This assumes that when deploying this Cloud Function, the 'backend' module
# (or relevant parts of it like config and services.vertex_ai_client)
# is included in the deployment package or accessible in the Python path.
try:
    from backend.config import settings
    from backend.services.vertex_ai_client import get_rag_data_service_client
except ImportError:
    logger_import_fallback = logging.getLogger(__name__)
    logger_import_fallback.warning(
        "Failed to import from 'backend' package. Using mock settings and client for RAG Import CF. "
        "Ensure 'backend' module is in PYTHONPATH or packaged for deployment."
    )
    class MockSettings:
        PROJECT_ID = os.environ.get("PROJECT_ID")
        VERTEX_AI_REGION = os.environ.get("VERTEX_AI_REGION", "us-central1")
        DEFAULT_RAG_CHUNK_SIZE = int(os.environ.get("DEFAULT_RAG_CHUNK_SIZE", 1000))
        DEFAULT_RAG_CHUNK_OVERLAP = int(os.environ.get("DEFAULT_RAG_CHUNK_OVERLAP", 200))
    settings = MockSettings()

    def get_rag_data_service_client(project_id=None, location=None):
        p_id = project_id or settings.PROJECT_ID
        loc = location or settings.VERTEX_AI_REGION
        if not p_id or not loc:
            # Log this critical failure for the mock setup
            logger_import_fallback.error("Mock get_rag_data_service_client: PROJECT_ID or VERTEX_AI_REGION not set.")
            raise ValueError("PROJECT_ID or VERTEX_AI_REGION not set for mock Vertex AI client.")
        client_options = {"api_endpoint": f"{loc}-aiplatform.googleapis.com"}
        return aiplatform.VertexRagDataServiceClient(client_options=client_options)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase_client: Client = None
if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
    try:
        supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
else:
    logger.warning("Supabase URL or Service Role Key not configured for RAG Import Cloud Function.")


@functions_framework.http
def rag_import_trigger(request):
    """
    HTTP-triggered Cloud Function (called by Cloud Tasks) to import a file into Vertex AI RAG.
    Receives payload: {"processing_id", "tenant_id", "gcs_uri_to_import", "original_filename", "file_type_for_parsing"}
    """
    if not supabase_client:
        logger.error("Supabase client not initialized. Cannot proceed.")
        return ("Internal Server Error: DB client not configured", 500)

    if request.method != 'POST':
        logger.warning(f"Received {request.method}, expected POST.")
        return ("Only POST requests are accepted", 405)

    try:
        payload = request.get_json(silent=True)
        if not payload:
            logger.error("No JSON payload received.")
            return ("Bad Request: No JSON payload", 400)

        processing_id_str = payload.get("processing_id")
        tenant_id_str = payload.get("tenant_id")
        gcs_uri_to_import = payload.get("gcs_uri_to_import")
        # original_filename = payload.get("original_filename") # For logging/display
        file_type_for_parsing = payload.get("file_type_for_parsing") # Original file type

        if not all([processing_id_str, tenant_id_str, gcs_uri_to_import, file_type_for_parsing]):
            logger.error(f"Missing required fields in payload: {payload}")
            return ("Bad Request: Missing required fields", 400)

        logger.info(f"RAG import trigger received for processing_id: {processing_id_str}, tenant: {tenant_id_str}, uri: {gcs_uri_to_import}")

    except Exception as e:
        logger.error(f"Error processing request JSON: {e}")
        return ("Bad Request: Invalid JSON", 400)

    try:
        # 1. Fetch RAG Corpus ID for the tenant
        tenant_data_response = supabase_client.table("tenants").select("rag_corpus_id, rag_corpus_display_name").eq("tenant_id", tenant_id_str).maybe_single().execute()

        if not tenant_data_response.data or not tenant_data_response.data.get("rag_corpus_id"):
            logger.error(f"RAG Corpus ID not found for tenant {tenant_id_str}.")
            supabase_client.table("rag_uploaded_files").update({
                "processing_status": "failed",
                "status_message": f"RAG Corpus ID not configured for tenant {tenant_id_str}."
            }).eq("processing_id", processing_id_str).execute()
            return ("Configuration error: RAG Corpus ID not found for tenant.", 500)

        rag_corpus_resource_name = tenant_data_response.data["rag_corpus_id"]
        logger.info(f"Found RAG Corpus: {rag_corpus_resource_name} for tenant {tenant_id_str}")

        rag_file_parsing_config = {}
        if file_type_for_parsing == "pdf":
            rag_file_parsing_config = aiplatform.RagFileParsingConfig(
                use_advanced_pdf_parsing=True
            )
            logger.info(f"Using advanced PDF parsing for {gcs_uri_to_import}")

        import_config = aiplatform.ImportRagFilesConfig(
            gcs_source=aiplatform.GcsSource(uris=[gcs_uri_to_import]),
            rag_file_parsing_config=rag_file_parsing_config if rag_file_parsing_config else None,
            rag_file_chunking_config=aiplatform.RagFileChunkingConfig(
                chunk_size=settings.DEFAULT_RAG_CHUNK_SIZE,
                chunk_overlap=settings.DEFAULT_RAG_CHUNK_OVERLAP
            )
        )
        logger.info(f"ImportConfig created: ChunkSize={settings.DEFAULT_RAG_CHUNK_SIZE}, ChunkOverlap={settings.DEFAULT_RAG_CHUNK_OVERLAP}")

        rag_data_client = get_rag_data_service_client()

        import_request = aiplatform.ImportRagFilesRequest(
            parent=rag_corpus_resource_name,
            import_rag_files_config=import_config
        )

        logger.info(f"Submitting ImportRagFilesRequest for {processing_id_str} to corpus {rag_corpus_resource_name}...")
        operation = rag_data_client.import_rag_files(request=import_request)

        logger.info(f"ImportRagFiles LRO started for {processing_id_str}: {operation.operation.name}")

        supabase_client.table("rag_uploaded_files").update({
            "processing_status": "importing",
            "status_message": f"Importing to Vertex AI RAG started. Operation: {operation.operation.name}",
            "vertex_ai_operation_name": operation.operation.name
        }).eq("processing_id", processing_id_str).execute()
        logger.info(f"DB status updated to 'importing' for {processing_id_str} with op name {operation.operation.name}")

        return (f"Import process started for {processing_id_str}. Operation: {operation.operation.name}", 202)

    except Exception as e:
        logger.error(f"Error during RAG import for {processing_id_str}: {e}", exc_info=True)
        try:
            supabase_client.table("rag_uploaded_files").update({
                "processing_status": "failed",
                "status_message": f"Error during Vertex AI RAG import: {str(e)}"
            }).eq("processing_id", processing_id_str).execute()
        except Exception as db_e:
            logger.error(f"Additionally failed to update DB to 'failed' for {processing_id_str}: {db_e}")
        return ("Internal Server Error during RAG import.", 500)
