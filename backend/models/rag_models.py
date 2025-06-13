# backend/models/rag_models.py
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid # Keep this for uuid.UUID type

class RagUploadedFileDetail(BaseModel):
    filename: str
    processing_id: uuid.UUID
    status_url: Optional[str] = None # Example: /api/v1/tenants/{tenant_id}/rag_files/status/{processing_id}

class RagFileUploadResponse(BaseModel):
    message: str
    processing_ids: List[uuid.UUID]
    uploaded_files: List[RagUploadedFileDetail]

class RagFileMetadata(BaseModel):
    processing_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    tenant_id: uuid.UUID
    uploaded_by_user_id: uuid.UUID
    original_filename: str
    gcs_upload_path: str
    gcs_processed_path: Optional[str] = None
    file_size: int # Bytes
    file_type: str # pdf, docx, csv, txt
    upload_timestamp: str # Will be set by DB default
    processing_status: str = "pending"
    status_message: Optional[str] = None
    vertex_ai_rag_file_id: Optional[str] = None
    vertex_ai_operation_name: Optional[str] = None

    # Pydantic V2 config
    model_config = ConfigDict(from_attributes=True) # if we decide to use it with ORM models directly
