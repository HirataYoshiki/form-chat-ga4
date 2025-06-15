import uuid
from typing import List, Optional, Tuple
from fastapi import UploadFile, HTTPException, BackgroundTasks, status
from fastapi.concurrency import run_in_threadpool
from supabase import Client as SupabaseSyncClient
from backend.config import settings
from backend.models.rag_models import RagFileUploadResponse, RagUploadedFileDetail, RagFileMetadata, RagProcessingStatus # Added RagProcessingStatus
import logging
import os

logger = logging.getLogger(__name__)

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
    # Actual GCS upload logic would go here
    # ...
    # Simulate task enqueue
    logger.info(f"Simulated Cloud Task enqueue for processing_id: {processing_id} with payload containing GCS path: {gcs_upload_path}")
    # Actual Cloud Task enqueue logic would go here
    # ...
    return gcs_upload_path, None


async def upload_files_for_rag(
    tenant_id: uuid.UUID,
    files: List[UploadFile],
    uploaded_by_user_id: uuid.UUID,
    db: SupabaseSyncClient,
    background_tasks: BackgroundTasks
) -> RagFileUploadResponse:
    uploaded_file_details: List[RagUploadedFileDetail] = []
    ALLOWED_FILE_TYPES_MAP = {'.pdf': 'pdf', '.txt': 'txt', '.md': 'md'}
    ALLOWED_MIME_TYPES_FOR_UPLOAD = ["application/pdf", "text/plain", "text/markdown"]
    MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024

    for file in files:
        original_filename = file.filename
        file_extension = os.path.splitext(original_filename)[1].lower()
        file_content_type = file.content_type

        # Basic validation
        if file_extension not in ALLOWED_FILE_TYPES_MAP or file_content_type not in ALLOWED_MIME_TYPES_FOR_UPLOAD:
            logger.warning(f"File type not allowed: {original_filename} ({file_content_type}, ext: {file_extension}) for tenant {tenant_id}")
            uploaded_file_details.append(RagUploadedFileDetail(
                original_filename=original_filename, processing_id=uuid.uuid4(), status_url="",
                message=f"File type {file_extension or file_content_type} not allowed. Allowed: {', '.join(ALLOWED_FILE_TYPES_MAP.keys())}"
            ))
            continue

        file_content = await file.read()
        file_size = len(file_content)

        if file_size > MAX_FILE_SIZE_BYTES:
            logger.warning(f"File too large: {original_filename} ({file_size} bytes) for tenant {tenant_id}")
            uploaded_file_details.append(RagUploadedFileDetail(
                original_filename=original_filename, processing_id=uuid.uuid4(), status_url="",
                message=f"File size {file_size} bytes exceeds limit of {MAX_FILE_SIZE_BYTES} bytes."
            ))
            continue

        file_type = ALLOWED_FILE_TYPES_MAP[file_extension]
        processing_id = uuid.uuid4()

        db_insert_payload = {
            "processing_id": str(processing_id), "tenant_id": str(tenant_id),
            "uploaded_by_user_id": str(uploaded_by_user_id), "original_filename": original_filename,
            "gcs_upload_path": "", "file_size": file_size, "file_type": file_type,
            "processing_status": RagProcessingStatus.PENDING_UPLOAD.value, # Use enum value
        }

        def db_insert_op():
            response = db.table("rag_uploaded_files").insert(db_insert_payload).execute()
            return response.data and len(response.data) > 0

        try:
            insert_success = await run_in_threadpool(db_insert_op)
            if not insert_success:
                logger.error(f"DB Error inserting initial metadata for {original_filename} (tenant {tenant_id})")
                uploaded_file_details.append(RagUploadedFileDetail(
                    original_filename=original_filename, processing_id=processing_id, status_url="",
                    message="Failed to create database record for file."
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
            original_filename=original_filename, content_type=file_content_type, file_type=file_type,
            uploaded_by_user_id=uploaded_by_user_id
        )

        # This URL should point to an endpoint that can fetch status using processing_id,
        # potentially the new get_rag_file_details via the router.
        # The router will need to be named for url_path_for.
        status_url = f"/api/v1/tenants/{tenant_id}/rag_files/{processing_id}/status" # Path for the new status endpoint
        uploaded_file_details.append(RagUploadedFileDetail(
            original_filename=original_filename, processing_id=processing_id, status_url=status_url
        ))

    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No files provided.")

    return RagFileUploadResponse(
        message="File upload process initiated. Check status URLs for individual file progress.",
        tenant_id=str(tenant_id),
        uploaded_files=uploaded_file_details
    )

async def list_rag_files_for_tenant(db: SupabaseSyncClient, tenant_id: uuid.UUID) -> List[RagFileMetadata]:
    logger.info(f"Listing RAG files for tenant_id: {tenant_id}")
    try:
        response = await run_in_threadpool(
            db.table("rag_uploaded_files")
            .select("processing_id, tenant_id, uploaded_by_user_id, original_filename, gcs_upload_path, gcs_processed_path, file_size, file_type, processing_status, status_message, upload_timestamp, last_processed_timestamp, vertex_ai_rag_file_id, vertex_ai_operation_name")
            .eq("tenant_id", str(tenant_id))
            .order("upload_timestamp", desc=True)
            .execute
        )
        if response.data:
            return [RagFileMetadata(**item) for item in response.data]
        return []
    except Exception as e:
        logger.error(f"Error listing RAG files for tenant {tenant_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve RAG file list.")

async def delete_rag_file_by_id(db: SupabaseSyncClient, tenant_id: uuid.UUID, processing_id: uuid.UUID) -> bool:
    logger.info(f"Attempting to delete RAG file with processing_id: {processing_id} for tenant_id: {tenant_id}")
    try:
        # TODO: Implement actual GCS file deletion and vector index cleanup.
        response = await run_in_threadpool(
            db.table("rag_uploaded_files")
            .delete()
            .eq("processing_id", str(processing_id))
            .eq("tenant_id", str(tenant_id))
            .execute
        )
        if response.data and len(response.data) > 0:
            logger.info(f"Successfully deleted RAG file record: {processing_id} for tenant {tenant_id}")
            return True
        else:
            logger.warning(f"RAG file not found for deletion or delete returned no data: processing_id {processing_id}, tenant_id {tenant_id}")
            return False
    except Exception as e:
        logger.error(f"Error deleting RAG file {processing_id} for tenant {tenant_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to delete RAG file due to server error: {processing_id}")

async def get_rag_file_details(db: SupabaseSyncClient, tenant_id: uuid.UUID, processing_id: uuid.UUID) -> Optional[RagFileMetadata]:
    logger.info(f"Fetching RAG file details for processing_id: {processing_id}, tenant_id: {tenant_id}")
    try:
        response = await run_in_threadpool(
            db.table("rag_uploaded_files")
            .select("processing_id, tenant_id, uploaded_by_user_id, original_filename, gcs_upload_path, gcs_processed_path, file_size, file_type, processing_status, status_message, upload_timestamp, last_processed_timestamp, vertex_ai_rag_file_id, vertex_ai_operation_name") # Explicitly select all fields from RagFileMetadata
            .eq("tenant_id", str(tenant_id))
            .eq("processing_id", str(processing_id))
            .maybe_single()
            .execute
        )
        if response.data:
            return RagFileMetadata(**response.data)
        return None
    except Exception as e:
        logger.error(f"Error fetching RAG file details for {processing_id}, tenant {tenant_id}: {e}", exc_info=True)
        return None # Let router handle not found
