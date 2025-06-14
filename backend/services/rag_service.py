import uuid
from typing import List, Optional, Tuple
from fastapi import UploadFile, HTTPException, BackgroundTasks, status # Added status
from fastapi.concurrency import run_in_threadpool
from supabase import Client as SupabaseSyncClient
# from google.cloud import storage
# from google.cloud import tasks_v2
from backend.config import settings
from backend.models.rag_models import RagFileUploadResponse, RagUploadedFileDetail, RagFileMetadata # Added RagFileMetadata
import logging
import os

logger = logging.getLogger(__name__)

# Placeholder for GCS upload and Cloud Tasks enqueue logic
async def _upload_to_gcs_and_enqueue_task(
    tenant_id: uuid.UUID,
    processing_id: uuid.UUID,
    file_content: bytes,
    original_filename: str,
    content_type: str,
    file_type: str,
    uploaded_by_user_id: uuid.UUID
) -> Tuple[str, Optional[str]]:
    gcs_upload_path = f"{tenant_id}/uploads/{processing_id}_{original_filename}"
    logger.info(f"Simulated GCS upload for {original_filename} to {gcs_upload_path}. Content type: {content_type}, File type: {file_type}")
    logger.info(f"Simulated Cloud Task enqueue for processing_id: {processing_id} with payload containing GCS path: {gcs_upload_path}")
    return gcs_upload_path, None


async def upload_files_for_rag(
    tenant_id: uuid.UUID,
    files: List[UploadFile],
    uploaded_by_user_id: uuid.UUID,
    db: SupabaseSyncClient,
    background_tasks: BackgroundTasks
) -> RagFileUploadResponse:

    uploaded_file_details: List[RagUploadedFileDetail] = []

    # Allowed extensions and their corresponding simple file types
    # This should align with what your document processing can handle
    ALLOWED_FILE_TYPES_MAP = {
        '.pdf': 'pdf',
        '.txt': 'txt',
        '.md': 'md',
        # Add more types as your backend processing supports them
        # '.docx': 'docx',
        # '.pptx': 'pptx',
        # '.xlsx': 'xlsx',
    }
    # Corresponding MIME types for initial check (can be broader)
    ALLOWED_MIME_TYPES_FOR_UPLOAD = [
        "application/pdf",
        "text/plain",
        "text/markdown",
        # "application/vnd.openxmlformats-officedocument.wordprocessingml.document", # docx
        # "application/vnd.openxmlformats-officedocument.presentationml.presentation", # pptx
        # "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" # xlsx
    ]
    MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024 # 10MB example

    for file in files:
        original_filename = file.filename
        file_extension = os.path.splitext(original_filename)[1].lower()

        if file.content_type not in ALLOWED_MIME_TYPES_FOR_UPLOAD or file_extension not in ALLOWED_FILE_TYPES_MAP:
            logger.warning(f"File type not allowed: {original_filename} ({file.content_type}, ext: {file_extension}) for tenant {tenant_id}")
            uploaded_file_details.append(RagUploadedFileDetail(
                original_filename=original_filename,
                processing_id=uuid.uuid4(), # Dummy ID for skipped file
                status_url="", # No status URL as it's not processed
                message=f"File type {file_extension or file.content_type} not allowed. Allowed: {', '.join(ALLOWED_FILE_TYPES_MAP.keys())}"
            ))
            continue

        file_content = await file.read()
        file_size = len(file_content)
        content_type = file.content_type

        if file_size > MAX_FILE_SIZE_BYTES:
            logger.warning(f"File too large: {original_filename} ({file_size} bytes) for tenant {tenant_id}")
            uploaded_file_details.append(RagUploadedFileDetail(
                original_filename=original_filename,
                processing_id=uuid.uuid4(), # Dummy ID for skipped file
                status_url="",
                message=f"File size {file_size} bytes exceeds limit of {MAX_FILE_SIZE_BYTES} bytes."
            ))
            continue

        file_type = ALLOWED_FILE_TYPES_MAP[file_extension]
        processing_id = uuid.uuid4()

        db_insert_payload = {
            "processing_id": str(processing_id),
            "tenant_id": str(tenant_id),
            "uploaded_by_user_id": str(uploaded_by_user_id),
            "original_filename": original_filename,
            "gcs_upload_path": "", # Will be updated by background task
            "file_size": file_size,
            "file_type": file_type,
            "processing_status": "pending_upload",
        }

        def db_insert_op():
            response = db.table("rag_uploaded_files").insert(db_insert_payload).execute()
            if response.data and len(response.data) > 0:
                logger.info(f"Initial DB record created for {original_filename} with processing_id {processing_id} for tenant {tenant_id}")
                return True
            else:
                error_detail = "Unknown error during DB insert"
                if hasattr(response, 'error') and response.error: error_detail = response.error.message
                elif hasattr(response, 'status_code') and response.status_code not in [200, 201]: error_detail = f"Status {response.status_code}"
                logger.error(f"DB Error inserting initial metadata for {original_filename} (tenant {tenant_id}): {error_detail}. Response: {str(response)}")
                return False

        try:
            insert_success = await run_in_threadpool(db_insert_op)
            if not insert_success:
                uploaded_file_details.append(RagUploadedFileDetail(
                    original_filename=original_filename, processing_id=processing_id, status_url="",
                    message="Failed to create initial database record."
                ))
                continue
        except Exception as e:
            logger.error(f"Exception during DB insert for {original_filename} (tenant {tenant_id}): {e}", exc_info=True)
            uploaded_file_details.append(RagUploadedFileDetail(
                original_filename=original_filename, processing_id=processing_id, status_url="",
                message=f"Internal error during DB record creation: {str(e)}"
            ))
            continue

        background_tasks.add_task(
            _upload_to_gcs_and_enqueue_task,
            tenant_id=tenant_id, processing_id=processing_id, file_content=file_content,
            original_filename=original_filename, content_type=content_type, file_type=file_type,
            uploaded_by_user_id=uploaded_by_user_id
        )

        status_url = f"/api/v1/rag_processing_jobs/{processing_id}/status" # Example, adjust as per actual router
        uploaded_file_details.append(RagUploadedFileDetail(
            original_filename=original_filename, # Corrected from filename=
            processing_id=str(processing_id), # Ensure string
            status_url=status_url
        ))

    if not files: # Check if the input list was empty
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No files provided in the upload request.")

    # If all files were invalid and uploaded_file_details only contains error messages,
    # the overall message should reflect that.
    # The current structure of RagFileUploadResponse might need adjustment if we want to clearly separate successfully enqueued files from failed ones.
    # For now, it returns all attempts.

    return RagFileUploadResponse(
        message="File upload process initiated. Check status URLs for individual file progress.",
        tenant_id=str(tenant_id), # Ensure string
        uploaded_files=uploaded_file_details
    )

async def list_rag_files_for_tenant(db: SupabaseSyncClient, tenant_id: uuid.UUID) -> List[RagFileMetadata]:
    logger.info(f"Listing RAG files for tenant_id: {tenant_id}")
    try:
        response = await run_in_threadpool(
            db.table("rag_uploaded_files")
            .select("processing_id, tenant_id, uploaded_by_user_id, original_filename, gcs_upload_path, file_size, file_type, processing_status, error_message, upload_timestamp, last_processed_timestamp") # Explicitly list columns
            .eq("tenant_id", str(tenant_id))
            .order("upload_timestamp", desc=True) # Supabase client uses desc=True
            .execute
        )
        if response.data:
            # Ensure all fields expected by RagFileMetadata are present or handled (e.g. with default values or Optional)
            return [RagFileMetadata(**item) for item in response.data]
        return []
    except Exception as e:
        logger.error(f"Error listing RAG files for tenant {tenant_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve RAG file list.")

async def delete_rag_file_by_id(db: SupabaseSyncClient, tenant_id: uuid.UUID, processing_id: uuid.UUID) -> bool:
    logger.info(f"Attempting to delete RAG file with processing_id: {processing_id} for tenant_id: {tenant_id}")
    try:
        # TODO: Implement actual GCS file deletion if required, before or after DB record.
        # This should be done in a background task or carefully managed for atomicity.
        # For GCS deletion:
        # 1. Get gcs_upload_path from DB for this processing_id and tenant_id.
        # 2. If record exists and gcs_upload_path is not empty, delete from GCS.
        #    Handle errors during GCS deletion (e.g., file not found in GCS is okay if DB record is being cleaned up).

        response = await run_in_threadpool(
            db.table("rag_uploaded_files")
            .delete()
            .eq("processing_id", str(processing_id))
            .eq("tenant_id", str(tenant_id))
            .execute
        )

        if response.data and len(response.data) > 0:
            logger.info(f"Successfully deleted RAG file record: {processing_id} for tenant {tenant_id}")
            # TODO: Trigger background task for vector index cleanup if necessary.
            return True
        else:
            # This means the record was not found for the given tenant_id and processing_id, or already deleted.
            logger.warning(f"RAG file not found for deletion or delete operation returned no data (already deleted?): processing_id {processing_id}, tenant_id {tenant_id}")
            return False

    except Exception as e:
        logger.error(f"Error deleting RAG file {processing_id} for tenant {tenant_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to delete RAG file due to server error: {processing_id}")

# Placeholder for get_rag_file_status (if needed directly by router, or handled by a separate job status endpoint)
# async def get_rag_file_status(db: SupabaseSyncClient, processing_id: uuid.UUID) -> Optional[RagFileMetadata]:
#     logger.info(f"Fetching status for RAG file processing_id: {processing_id}")
#     try:
#         response = await run_in_threadpool(
#             db.table("rag_uploaded_files").select("*").eq("processing_id", str(processing_id)).maybe_single().execute
#         )
#         if response.data:
#             return RagFileMetadata(**response.data)
#         return None
#     except Exception as e:
#         logger.error(f"Error fetching status for RAG file {processing_id}: {e}", exc_info=True)
#         # Depending on use, might raise HTTPException or return None/error indicator
#         return None
