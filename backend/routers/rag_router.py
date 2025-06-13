import uuid
import logging # Added logging
from typing import List, Annotated # Annotated was missing in prompt for this file
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks, Path, status
# from supabase_py_async import AsyncClient # Assuming async client - current get_supabase_client is sync
from supabase import Client as SupabaseSyncClient # Using sync client for now

from backend.services.rag_service import upload_files_for_rag
from backend.models.rag_models import RagFileUploadResponse
# from backend.dependencies import get_supabase_client, get_current_active_user # Incorrect path for dependencies
from backend.db import get_supabase_client # Correct path
from backend.auth import AuthenticatedUser, get_current_active_user # Correct path and UserInDB -> AuthenticatedUser

logger = logging.getLogger(__name__) # Added logger

router = APIRouter(
    prefix="/api/v1/tenants/{tenant_id}/rag_files",
    tags=["RAG Files"],
)

@router.post("", response_model=RagFileUploadResponse, status_code=status.HTTP_202_ACCEPTED) # Changed status to 202
async def upload_rag_documents_endpoint( # Renamed for clarity
    tenant_id: Annotated[uuid.UUID, Path(description="The ID of the tenant to upload files for")],
    files: List[UploadFile] = File(..., description="Files to be uploaded for RAG."),
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    # Use SupabaseSyncClient based on current get_supabase_client
    db: SupabaseSyncClient = Depends(get_supabase_client),
    background_tasks: BackgroundTasks = Depends() # Correct way to inject BackgroundTasks
):
    if str(current_user.tenant_id) != str(tenant_id) and current_user.app_role != "superuser":
        logger.warning(
            f"User {current_user.id} (tenant: {current_user.tenant_id}, role: {current_user.app_role}) "
            f"attempted to upload RAG files for tenant {tenant_id}."
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to upload files for this tenant.")

    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No files provided.")

    logger.info(f"User {current_user.id} uploading {len(files)} file(s) for tenant {tenant_id}.")

    try:
        response_payload = await upload_files_for_rag(
            tenant_id=tenant_id,
            files=files,
            uploaded_by_user_id=uuid.UUID(current_user.id), # Convert user.id (str) to UUID
            db=db,
            background_tasks=background_tasks
        )

        # Add status URLs to response details
        for detail in response_payload.uploaded_files:
            detail.status_url = router.url_path_for("get_rag_file_status_endpoint", tenant_id=str(tenant_id), processing_id=str(detail.processing_id))

        return response_payload
    except HTTPException as http_exc:
        logger.warning(f"HTTPException during RAG file upload for tenant {tenant_id} by user {current_user.id}: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error in upload_rag_documents endpoint for tenant {tenant_id} by user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred during file upload.")


# Placeholder for status endpoint
@router.get("/status/{processing_id}",
            # response_model=RagFileStatusResponse, # Define this model later
            tags=["RAG Files"],
            name="get_rag_file_status_endpoint" # Added name for url_path_for
            )
async def get_rag_file_status_endpoint( # Renamed for clarity
    tenant_id: Annotated[uuid.UUID, Path(description="Tenant ID")],
    processing_id: Annotated[uuid.UUID, Path(description="Processing ID of the file upload")],
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: SupabaseSyncClient = Depends(get_supabase_client),
):
    if str(current_user.tenant_id) != str(tenant_id) and current_user.app_role != "superuser":
        logger.warning(
            f"User {current_user.id} (tenant: {current_user.tenant_id}, role: {current_user.app_role}) "
            f"attempted to access RAG file status {processing_id} for tenant {tenant_id}."
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view status for this tenant.")

    logger.info(f"User {current_user.id} requesting status for processing_id {processing_id} for tenant {tenant_id}.")

    try:
        # Logic to fetch status from rag_uploaded_files table using processing_id and tenant_id
        response = db.table("rag_uploaded_files").select("processing_id, original_filename, processing_status, status_message, upload_timestamp, vertex_ai_rag_file_id").eq("processing_id", str(processing_id)).eq("tenant_id", str(tenant_id)).maybe_single().execute()

        if not response.data:
            logger.warning(f"RAG file status not found for processing_id {processing_id}, tenant {tenant_id}.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File processing record not found.")
        return response.data
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error fetching RAG file status for processing_id {processing_id}, tenant {tenant_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch file processing status.")
