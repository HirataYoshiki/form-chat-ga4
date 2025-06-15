# backend/models/rag_models.py
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from enum import Enum # Added

class RagProcessingStatus(str, Enum):
    PENDING_UPLOAD = "pending_upload"
    UPLOAD_TO_GCS_FAILED = "upload_to_gcs_failed" # Not used yet, but good for future
    PENDING_PREPROCESS = "pending_preprocess"
    PREPROCESSING = "preprocessing"
    PREPROCESS_FAILED = "preprocess_failed"
    PENDING_INDEXING = "pending_indexing"
    INDEXING = "indexing"
    COMPLETED = "completed"
    FAILED = "failed"
    DELETING = "deleting"
    DELETED = "deleted"

class RagUploadedFileDetail(BaseModel):
    original_filename: str # Changed from filename to original_filename
    processing_id: uuid.UUID
    status_url: Optional[str] = None

class RagFileUploadResponse(BaseModel):
    message: str
    tenant_id: str # Was uuid.UUID, but service returns str(tenant_id)
    uploaded_files: List[RagUploadedFileDetail]

class RagFileMetadata(BaseModel):
    processing_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    tenant_id: uuid.UUID
    uploaded_by_user_id: uuid.UUID
    original_filename: str
    gcs_upload_path: Optional[str] = None # Made optional as it's updated later
    gcs_processed_path: Optional[str] = None
    file_size: int
    file_type: str
    upload_timestamp: str # Assuming this is datetime as string from DB
    processing_status: RagProcessingStatus = RagProcessingStatus.PENDING_UPLOAD
    status_message: Optional[str] = None
    vertex_ai_rag_file_id: Optional[str] = None
    vertex_ai_operation_name: Optional[str] = None
    # Ensure last_processed_timestamp is also here if it's in the DB select
    last_processed_timestamp: Optional[str] = None


    model_config = ConfigDict(from_attributes=True, use_enum_values=True) # use_enum_values for response models
