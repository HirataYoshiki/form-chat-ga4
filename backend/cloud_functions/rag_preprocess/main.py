import functions_framework
from google.cloud import storage
from google.cloud import tasks_v2
from supabase import create_client, Client
import os
import uuid
import json
import logging
import io
from docx import Document # For DOCX
import csv # For CSV

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize clients globally - consider best practices for client reuse in Cloud Functions
try:
    storage_client = storage.Client()
    tasks_client = tasks_v2.CloudTasksClient()
except Exception as e:
    logger.error(f"Failed to initialize Google Cloud clients: {e}")
    storage_client = None
    tasks_client = None

# Supabase client setup - ensure these ENV VARS are set in the CF environment
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase_client: Client = None
if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
    try:
        supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
else:
    logger.warning("Supabase URL or Service Role Key not configured for Cloud Function.")

# Configuration from environment variables
RAG_GCS_BUCKET_PROCESSED_NAME = os.environ.get("RAG_GCS_BUCKET_PROCESSED")
CLOUD_TASKS_QUEUE_PATH = os.environ.get("RAG_IMPORT_TASK_QUEUE_PATH") # e.g., projects/PROJECT_ID/locations/LOCATION/queues/QUEUE_ID
RAG_IMPORT_FUNCTION_URL = os.environ.get("RAG_IMPORT_FUNCTION_URL") # URL for the next stage (import to Vertex RAG)

@functions_framework.cloud_event
def process_uploaded_rag_file(cloud_event):
    """
    Cloud Function triggered by GCS upload to preprocess files for RAG.
    - Extracts text from DOCX/CSV.
    - Saves processed file to another GCS location.
    - Updates database status.
    - Enqueues a task for the next stage (import to Vertex AI RAG).
    """
    if not all([storage_client, tasks_client, supabase_client, RAG_GCS_BUCKET_PROCESSED_NAME, CLOUD_TASKS_QUEUE_PATH, RAG_IMPORT_FUNCTION_URL]):
        logger.error("Cloud Function is not properly configured. Missing clients or ENV VARS.")
        return # Or raise an exception to retry if appropriate

    data = cloud_event.data
    source_bucket_name = data.get("bucket")
    source_blob_name = data.get("name") # Full path in GCS, e.g., <tenant_id>/uploads/<processing_id>_<original_filename>.<ext>

    if not source_bucket_name or not source_blob_name:
        logger.error("Invalid GCS event data: missing bucket or name.")
        return

    logger.info(f"Processing file: gs://{source_bucket_name}/{source_blob_name}")
    processing_id_str = None # Initialize to handle potential extraction failure

    try:
        # 1. Extract metadata from the source_blob_name
        path_parts = source_blob_name.split('/')
        if len(path_parts) < 3:
            logger.error(f"Invalid GCS path structure: {source_blob_name}. Expected <tenant_id>/uploads/<processing_id>_<filename>.<ext>")
            return

        tenant_id_str = path_parts[0]
        # uploads_folder = path_parts[1] # Should be 'uploads'

        filename_with_processing_id = path_parts[-1] # <processing_id>_<original_filename>.<ext>

        try:
            processing_id_str = filename_with_processing_id.split('_', 1)[0]
            uuid.UUID(processing_id_str) # Validate if it's a UUID
        except (IndexError, ValueError) as e:
            logger.error(f"Could not extract valid processing_id from filename {filename_with_processing_id}: {e}")
            return

        original_filename_with_ext = filename_with_processing_id[len(processing_id_str)+1:]
        file_ext = os.path.splitext(original_filename_with_ext)[1].lower().strip('.')

        logger.info(f"Extracted: tenant_id='{tenant_id_str}', processing_id='{processing_id_str}', original_filename='{original_filename_with_ext}', ext='{file_ext}'")

        # 2. Update DB status to 'preprocessing'
        try:
            supabase_client.table("rag_uploaded_files").update({
                "processing_status": "preprocessing",
                "status_message": "File picked up for preprocessing."
            }).eq("processing_id", processing_id_str).eq("tenant_id", tenant_id_str).execute() # Added tenant_id for safety
            logger.info(f"DB status updated to 'preprocessing' for {processing_id_str}")
        except Exception as e:
            logger.error(f"Failed to update DB status to 'preprocessing' for {processing_id_str}: {e}")

        # 3. Download file from GCS
        source_blob = storage_client.bucket(source_bucket_name).blob(source_blob_name)
        if not source_blob.exists():
            logger.error(f"Source blob gs://{source_bucket_name}/{source_blob_name} not found.")
            supabase_client.table("rag_uploaded_files").update({
                "processing_status": "failed",
                "status_message": "Source file not found in GCS for preprocessing."
            }).eq("processing_id", processing_id_str).eq("tenant_id", tenant_id_str).execute()
            return

        file_bytes = source_blob.download_as_bytes()
        logger.info(f"Downloaded {len(file_bytes)} bytes from gs://{source_bucket_name}/{source_blob_name}")

        processed_text_content = None
        target_file_ext = file_ext

        # 4. Perform preprocessing based on file type
        if file_ext == "docx":
            try:
                logger.info(f"Starting DOCX processing for {processing_id_str}")
                document = Document(io.BytesIO(file_bytes))
                processed_text_content = "\n".join([para.text for para in document.paragraphs if para.text.strip()])
                target_file_ext = "txt"
                logger.info(f"DOCX content extracted for {processing_id_str}")
            except Exception as e:
                logger.error(f"Failed to parse DOCX file {original_filename_with_ext}: {e}")
                supabase_client.table("rag_uploaded_files").update({
                    "processing_status": "failed",
                    "status_message": f"DOCX parsing failed: {str(e)}"
                }).eq("processing_id", processing_id_str).eq("tenant_id", tenant_id_str).execute()
                return
        elif file_ext == "csv":
            try:
                logger.info(f"Starting CSV processing for {processing_id_str}")
                file_text = file_bytes.decode('utf-8')
                csv_reader = csv.reader(io.StringIO(file_text))
                text_parts = []
                for row in csv_reader:
                    text_parts.append(", ".join(row))
                processed_text_content = "\n".join(text_parts)
                target_file_ext = "txt"
                logger.info(f"CSV content extracted for {processing_id_str}")
            except Exception as e:
                logger.error(f"Failed to parse CSV file {original_filename_with_ext}: {e}")
                supabase_client.table("rag_uploaded_files").update({
                    "processing_status": "failed",
                    "status_message": f"CSV parsing failed: {str(e)}"
                }).eq("processing_id", processing_id_str).eq("tenant_id", tenant_id_str).execute()
                return
        elif file_ext == "txt":
            logger.info(f"TXT file {processing_id_str} requires no text extraction.")
            processed_text_content = file_bytes.decode('utf-8')
        elif file_ext == "pdf":
            logger.info(f"PDF file {processing_id_str} will be processed by Vertex AI RAG directly.")
        else:
            logger.warning(f"Unsupported file type '{file_ext}' for {processing_id_str}. Passing original.")

        gcs_uri_to_import = ""
        processed_blob_name_for_db = None

        if processed_text_content is not None and file_ext in ["docx", "csv", "txt"]:
            processed_blob_name = f"{tenant_id_str}/processed/{processing_id_str}_{os.path.splitext(original_filename_with_ext)[0]}.{target_file_ext}"
            processed_blob = storage_client.bucket(RAG_GCS_BUCKET_PROCESSED_NAME).blob(processed_blob_name)
            processed_blob.upload_from_string(processed_text_content.encode('utf-8'), content_type=f'text/{target_file_ext}')
            gcs_uri_to_import = f"gs://{RAG_GCS_BUCKET_PROCESSED_NAME}/{processed_blob_name}"
            processed_blob_name_for_db = processed_blob_name
            logger.info(f"Processed text for {processing_id_str} uploaded to {gcs_uri_to_import}")
        elif file_ext == "pdf":
            gcs_uri_to_import = f"gs://{source_bucket_name}/{source_blob_name}"
            logger.info(f"PDF {processing_id_str} will be imported from original GCS path: {gcs_uri_to_import}")
        else:
            logger.error(f"File {processing_id_str} with ext {file_ext} cannot be processed for import.")
            supabase_client.table("rag_uploaded_files").update({
                "processing_status": "failed",
                "status_message": f"Unsupported file type for RAG processing: {file_ext}"
            }).eq("processing_id", processing_id_str).eq("tenant_id", tenant_id_str).execute()
            return

        db_update_payload = {
            "processing_status": "pending_import",
            "status_message": "Preprocessing complete, enqueued for Vertex AI RAG import.",
        }
        if processed_blob_name_for_db:
             db_update_payload["gcs_processed_path"] = processed_blob_name_for_db

        supabase_client.table("rag_uploaded_files").update(db_update_payload).eq("processing_id", processing_id_str).eq("tenant_id", tenant_id_str).execute()
        logger.info(f"DB status updated to 'pending_import' for {processing_id_str}")

        task_payload = {
            "processing_id": processing_id_str,
            "tenant_id": tenant_id_str,
            "gcs_uri_to_import": gcs_uri_to_import,
            "original_filename": original_filename_with_ext,
            "file_type_for_parsing": file_ext
        }

        task = tasks_v2.types.Task(
            http_request=tasks_v2.types.HttpRequest(
                http_method=tasks_v2.types.HttpMethod.POST,
                url=RAG_IMPORT_FUNCTION_URL,
                headers={"Content-Type": "application/json"},
                body=json.dumps(task_payload).encode('utf-8'),
            )
        )
        tasks_client.create_task(parent=CLOUD_TASKS_QUEUE_PATH, task=task)
        logger.info(f"Task enqueued for {processing_id_str} to import {gcs_uri_to_import}")

    except Exception as e:
        logger.error(f"Unhandled error processing file gs://{source_bucket_name}/{source_blob_name}: {e}", exc_info=True)
        try:
            if processing_id_str: # Check if processing_id_str was determined
                supabase_client.table("rag_uploaded_files").update({
                    "processing_status": "failed",
                    "status_message": f"Unhandled error during preprocessing: {str(e)}"
                }).eq("processing_id", processing_id_str).eq("tenant_id", tenant_id_str).execute()
        except Exception as db_e:
            logger.error(f"Additionally failed to update DB status on unhandled error for {source_blob_name}: {db_e}")
        # Re-raise the exception to allow Cloud Functions to handle retries if configured
        raise
