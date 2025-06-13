import uuid
from typing import List, Optional, Tuple
from fastapi import UploadFile, HTTPException, BackgroundTasks
from fastapi.concurrency import run_in_threadpool # Added
# from supabase_py_async import AsyncClient
from supabase import Client as SupabaseSyncClient
# from google.cloud import storage
# from google.cloud import tasks_v2
from backend.config import settings
from backend.models.rag_models import RagFileUploadResponse, RagUploadedFileDetail
import logging
import os

logger = logging.getLogger(__name__)

# Placeholder for GCS upload and Cloud Tasks enqueue logic
async def _upload_to_gcs_and_enqueue_task(
    tenant_id: uuid.UUID,
    processing_id: uuid.UUID,
    file_content: bytes, # Pass file content instead of UploadFile object
    original_filename: str,
    content_type: str, # Pass content_type
    file_type: str, # pdf, docx etc.
    uploaded_by_user_id: uuid.UUID
) -> Tuple[str, Optional[str]]: # Returns (gcs_upload_path, error_message or None)
    gcs_upload_path = f"{tenant_id}/uploads/{processing_id}_{original_filename}"

    # Simulate GCS Upload (actual implementation needed)
    # storage_client = storage.Client()
    # bucket = storage_client.bucket(settings.RAG_GCS_BUCKET_UPLOADS)
    # blob = bucket.blob(gcs_upload_path)
    # try:
    #     await blob.upload_from_string(file_content, content_type=content_type) # Async upload if available
    # except Exception as e:
    #     logger.error(f"Failed to upload {original_filename} to GCS: {e}")
    #     return "", str(e)

    logger.info(f"Simulated GCS upload for {original_filename} to {gcs_upload_path}. Content type: {content_type}, File type: {file_type}")

    # Simulate Cloud Tasks Enqueue (actual implementation needed)
    # tasks_client = tasks_v2.CloudTasksAsyncClient()
    # task_payload = {
    #     "processing_id": str(processing_id),
    #     "tenant_id": str(tenant_id),
    #     "gcs_upload_path": gcs_upload_path,
    #     "original_filename": original_filename,
    #     "file_type": file_type,
    #     "uploaded_by_user_id": str(uploaded_by_user_id)
    # }
    # # task = { ... payload: task_payload ... }
    # # await tasks_client.create_task(parent=queue_path, task=task)
    logger.info(f"Simulated Cloud Task enqueue for processing_id: {processing_id} with payload containing GCS path: {gcs_upload_path}")

    return gcs_upload_path, None


async def upload_files_for_rag(
    tenant_id: uuid.UUID,
    files: List[UploadFile],
    uploaded_by_user_id: uuid.UUID,
    db: SupabaseSyncClient, # Supabase sync client as per current db.py
    background_tasks: BackgroundTasks
) -> RagFileUploadResponse:

    processing_ids: List[uuid.UUID] = []
    uploaded_file_details: List[RagUploadedFileDetail] = []

    allowed_mime_types = {
        "application/pdf": "pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
        "text/csv": "csv",
        "text/plain": "txt"
    }
    MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024

    for file in files:
        if file.content_type not in allowed_mime_types:
            logger.warning(f"File type not allowed: {file.filename} ({file.content_type}) for tenant {tenant_id}")
            # For now, skipping invalid files, consider returning error details
            continue

        # Read file content once
        file_content = await file.read()
        file_size = len(file_content)
        content_type = file.content_type # Get content_type from UploadFile

        if file_size > MAX_FILE_SIZE_BYTES:
            logger.warning(f"File too large: {file.filename} ({file_size} bytes) for tenant {tenant_id}")
            continue

        file_type = allowed_mime_types[content_type] # Use content_type for mapping
        original_filename = file.filename
        processing_id = uuid.uuid4()

        db_insert_payload = {
            "processing_id": str(processing_id),
            "tenant_id": str(tenant_id),
            "uploaded_by_user_id": str(uploaded_by_user_id),
            "original_filename": original_filename,
            "gcs_upload_path": "",
            "file_size": file_size,
            "file_type": file_type,
            "processing_status": "pending_upload",
        }

        def db_insert_op():
            # This function will be run in a thread pool
            response = db.table("rag_uploaded_files").insert(db_insert_payload).execute()
            if response.data and len(response.data) > 0:
                logger.info(f"Initial DB record created for {original_filename} with processing_id {processing_id} for tenant {tenant_id}")
                return True # Indicate success
            else:
                error_detail = "Unknown error"
                if hasattr(response, 'error') and response.error:
                    error_detail = response.error.message
                elif hasattr(response, 'status_code') and response.status_code not in [200, 201]:
                    error_detail = f"Status {response.status_code}"

                error_detail = "Unknown error during DB insert"
                if hasattr(response, 'error') and response.error:
                    error_detail = response.error.message
                elif hasattr(response, 'status_code') and response.status_code not in [200, 201]: # Check for actual error status
                    error_detail = f"Status {response.status_code}"
                logger.error(f"DB Error inserting initial metadata for {original_filename} (tenant {tenant_id}): {error_detail}. Response: {str(response)}")
                return False # Indicate failure

        try:
            insert_success = await run_in_threadpool(db_insert_op)
            if not insert_success:
                logger.warning(f"Skipping file {original_filename} due to DB insert failure for tenant {tenant_id}.")
                continue
        except Exception as e:
            logger.error(f"Exception during threadpool execution of DB insert for {original_filename} (tenant {tenant_id}): {e}", exc_info=True)
            continue

        # Add GCS upload and Task enqueue to background
        background_tasks.add_task(
            _upload_to_gcs_and_enqueue_task,
            tenant_id=tenant_id,
            processing_id=processing_id,
            file_content=file_content,
            original_filename=original_filename,
            content_type=content_type, # Pass the extracted content_type
            file_type=file_type,
            uploaded_by_user_id=uploaded_by_user_id
        )

        # Note: DB updates for gcs_upload_path and status to 'pending_processing'
        # would ideally happen in the background task *after* successful GCS upload.
        # The placeholder _upload_to_gcs_and_enqueue_task doesn't do this.

        processing_ids.append(processing_id)
        uploaded_file_details.append(RagUploadedFileDetail(
            filename=original_filename,
            processing_id=processing_id,
            # status_url will be generated in the router
        ))

    if not uploaded_file_details:
        # This means no files were valid or all initial DB writes/uploads failed
        # Raise HTTPException here as it's a client issue (no valid files) or server pre-processing issue
        raise HTTPException(status_code=400, detail="No valid files were processed. Check file types and sizes.")

    return RagFileUploadResponse(
        message="Files received and enqueued for processing.",
        processing_ids=processing_ids,
        uploaded_files=uploaded_file_details
    )
