from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional
from enum import Enum

class DocumentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class DocumentType(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    PPTX = "pptx"

class DocumentBase(BaseModel):
    filename: str
    file_type: DocumentType
    file_size: int

class DocumentCreate(DocumentBase):
    user_id: str
    file_path: str
    original_filename: str
    mime_type: str

class DocumentResponse(BaseModel):
    id: str
    filename: str
    original_filename: str
    file_type: str
    file_size: int
    status: DocumentStatus
    error_message: Optional[str] = None
    page_count: Optional[int] = None
    word_count: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class DocumentUploadResponse(BaseModel):
    message: str
    document: DocumentResponse

class DocumentList(BaseModel):
    documents: list[DocumentResponse]
    total_count: int