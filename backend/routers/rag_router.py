import uuid
import logging
from typing import List, Annotated
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks, Path, status
from supabase import Client as SupabaseSyncClient

from backend.services.rag_service import upload_files_for_rag, list_rag_files_for_tenant, delete_rag_file_by_id # Added new imports
from backend.models.rag_models import RagFileUploadResponse, RagFileMetadata # Added RagFileMetadata
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
            uploaded_by_user_id=uuid.UUID(current_user.id),
            db=db,
            background_tasks=background_tasks
        )
        # The status_url is now correctly formed in the service layer based on a generic path.
        # No need to re-generate it here if the service provides the correct one.
        # If the service provides a relative path or needs router.url_path_for, adjust accordingly.
        # For now, assuming service provides the full or correct relative path for status_url.
        return response_payload
    except HTTPException as http_exc:
        logger.warning(f"HTTPException during RAG file upload for tenant {tenant_id} by user {current_user.id}: {http_exc.detail}")
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
    # Authorization: Allow superuser OR if the user's tenant_id matches the path tenant_id
    if current_user.app_role != "superuser" and (not current_user.tenant_id or str(current_user.tenant_id) != str(tenant_id)):
        logger.warning(
            f"User {current_user.id} (tenant: {current_user.tenant_id}, role: {current_user.app_role}) "
            f"attempted to list RAG files for unauthorized tenant {tenant_id}."
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to list files for this tenant.")

    logger.info(f"User {current_user.id} listing RAG files for tenant {tenant_id}.")
    return await list_rag_files_for_tenant(db, tenant_id)

@router.delete("/{processing_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file_endpoint(
    tenant_id: Annotated[uuid.UUID, Path(description="The ID of the tenant")],
    processing_id: Annotated[uuid.UUID, Path(description="The Processing ID of the file to delete")],
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: SupabaseSyncClient = Depends(get_supabase_client)
):
    # Authorization: Allow superuser OR if the user's tenant_id matches the path tenant_id
    if current_user.app_role != "superuser" and (not current_user.tenant_id or str(current_user.tenant_id) != str(tenant_id)):
        logger.warning(
            f"User {current_user.id} (tenant: {current_user.tenant_id}, role: {current_user.app_role}) "
            f"attempted to delete RAG file {processing_id} for unauthorized tenant {tenant_id}."
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete files for this tenant.")

    logger.info(f"User {current_user.id} attempting to delete RAG file {processing_id} for tenant {tenant_id}.")
    success = await delete_rag_file_by_id(db, tenant_id, processing_id)
    if not success:
        # The service function returns False if file not found for deletion, or True if deleted.
        # It raises HTTPException for server errors during the delete process.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found or already deleted.")
    return None # For 204 No Content response

# The status endpoint below is for a specific file's processing status.
# Note: The `upload_files_for_rag` service now generates status_url like "/api/v1/rag_processing_jobs/{processing_id}/status".
# This implies that a *different router* handles that path, not this one.
# This current router is prefixed with /api/v1/tenants/{tenant_id}/rag_files.
# For consistency, if this router were to have a status endpoint for a *file within a tenant's context*,
# it might be GET /{processing_id}/status.
# The existing endpoint below seems to be a duplicate or misplaced status check if we consider the service's generated URL.
# I will comment it out for now as the task is to add list and delete, and the status URL generated by service points elsewhere.

# @router.get("/status/{processing_id}", # This path would be /api/v1/tenants/{tenant_id}/rag_files/status/{processing_id}
#             # response_model=RagFileMetadata, # Assuming RagFileMetadata can represent status
#             tags=["RAG Files"],
#             name="get_rag_file_status_endpoint_within_tenant_context"
#             )
# async def get_rag_file_status_within_tenant_context_endpoint(
#     tenant_id: Annotated[uuid.UUID, Path(description="Tenant ID")],
#     processing_id: Annotated[uuid.UUID, Path(description="Processing ID of the file upload")],
#     current_user: AuthenticatedUser = Depends(get_current_active_user),
#     db: SupabaseSyncClient = Depends(get_supabase_client),
# ):
#     if str(current_user.tenant_id) != str(tenant_id) and current_user.app_role != "superuser":
#         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view status for this tenant.")
#     logger.info(f"User {current_user.id} requesting status for processing_id {processing_id} for tenant {tenant_id} (within tenant context).")
#     # This would need a service function like `get_rag_file_details`
#     # file_details = await get_rag_file_details(db, tenant_id, processing_id) # Example
#     # if not file_details:
#     #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File processing record not found for this tenant.")
#     # return file_details
#     # For now, returning a placeholder as service function is not defined for this specific path structure.
#     raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Status endpoint per file not fully implemented here yet.")
