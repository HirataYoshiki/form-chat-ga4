import uuid
import logging
from typing import List, Annotated
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks, Path, status
from supabase import Client as SupabaseSyncClient

from backend.services.rag_service import (
    upload_files_for_rag,
    list_rag_files_for_tenant,
    delete_rag_file_by_id,
    get_rag_file_details # Added import
)
from backend.models.rag_models import RagFileUploadResponse, RagFileMetadata
from backend.db import get_supabase_client
from backend.auth import AuthenticatedUser, get_current_active_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/tenants/{tenant_id}/rag_files",
    tags=["RAG Files"],
)

@router.post("", response_model=RagFileUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_rag_documents_endpoint(
    tenant_id: Annotated[uuid.UUID, Path(description="The ID of the tenant to upload files for")],
    files: List[UploadFile] = File(..., description="Files to be uploaded for RAG."),
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: SupabaseSyncClient = Depends(get_supabase_client),
    background_tasks: BackgroundTasks = Depends()
):
    if str(current_user.tenant_id) != str(tenant_id) and current_user.app_role != "superuser":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to upload files for this tenant.")

    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No files provided.")

    logger.info(f"User {current_user.id} uploading {len(files)} file(s) for tenant {tenant_id}.")

    try:
        response_payload = await upload_files_for_rag(
            tenant_id=tenant_id,
            files=files,
            uploaded_by_user_id=uuid.UUID(current_user.id),
            db=db,
            background_tasks=background_tasks
        )

        # Update status_url for each file using the new endpoint name
        for detail in response_payload.uploaded_files:
            if detail.processing_id: # Ensure processing_id is valid before creating URL
                 # Using relative path from this router's prefix for clarity if frontend reconstructs full URL
                detail.status_url = router.url_path_for("get_rag_file_status_for_tenant", tenant_id=str(tenant_id), processing_id=str(detail.processing_id))
            else:
                detail.status_url = "" # Or some indicator that status URL isn't applicable

        return response_payload
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error in upload_rag_documents endpoint for tenant {tenant_id} by user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred during file upload.")

@router.get("", response_model=List[RagFileMetadata])
async def list_files_for_tenant_endpoint(
    tenant_id: Annotated[uuid.UUID, Path(description="The ID of the tenant to list files for")],
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: SupabaseSyncClient = Depends(get_supabase_client)
):
    if current_user.app_role != "superuser" and (not current_user.tenant_id or str(current_user.tenant_id) != str(tenant_id)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to list files for this tenant.")

    logger.info(f"User {current_user.id} listing RAG files for tenant {tenant_id}.")
    return await list_rag_files_for_tenant(db, tenant_id)

@router.get("/{processing_id}/status",
            response_model=RagFileMetadata,
            tags=["RAG Files"],
            name="get_rag_file_status_for_tenant") # Name for url_path_for
async def get_rag_file_status_endpoint(
    tenant_id: Annotated[uuid.UUID, Path(description="Tenant ID")],
    processing_id: Annotated[uuid.UUID, Path(description="Processing ID of the file upload")],
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: SupabaseSyncClient = Depends(get_supabase_client),
):
    if current_user.app_role != "superuser" and (not current_user.tenant_id or str(current_user.tenant_id) != str(tenant_id)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view status for this tenant's file.")

    logger.info(f"User {current_user.id} requesting status for RAG file {processing_id} of tenant {tenant_id}.")

    file_details = await get_rag_file_details(db, tenant_id, processing_id)
    if not file_details:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"RAG file with processing_id {processing_id} not found for tenant {tenant_id}.")
    return file_details

@router.delete("/{processing_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file_endpoint(
    tenant_id: Annotated[uuid.UUID, Path(description="The ID of the tenant")],
    processing_id: Annotated[uuid.UUID, Path(description="The Processing ID of the file to delete")],
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: SupabaseSyncClient = Depends(get_supabase_client)
):
    if current_user.app_role != "superuser" and (not current_user.tenant_id or str(current_user.tenant_id) != str(tenant_id)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete files for this tenant.")

    logger.info(f"User {current_user.id} attempting to delete RAG file {processing_id} for tenant {tenant_id}.")
    success = await delete_rag_file_by_id(db, tenant_id, processing_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found or already deleted.")
    return None
