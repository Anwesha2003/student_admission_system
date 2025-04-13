from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

class DocumentType(str, Enum):
    TRANSCRIPT = "transcript"
    ID_PROOF = "id_proof"
    RECOMMENDATION_LETTER = "recommendation_letter"
    STATEMENT_OF_PURPOSE = "statement_of_purpose"
    RESUME = "resume"
    OTHER = "other"

class VerificationStatus(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    NEEDS_CLARIFICATION = "needs_clarification"

class DocumentCreate(BaseModel):
    student_id: str
    admission_id: str
    document_type: DocumentType
    file_name: str
    file_path: str
    uploaded_date: datetime = Field(default_factory=datetime.now)
    
    class Config:
        schema_extra = {
            "example": {
                "student_id": "S12345",
                "admission_id": "ADM12345",
                "document_type": "transcript",
                "file_name": "academic_transcript.pdf",
                "file_path": "/uploads/S12345/academic_transcript.pdf",
                "uploaded_date": "2025-01-15T12:00:00"
            }
        }

class Document(DocumentCreate):
    id: str
    verification_status: VerificationStatus = VerificationStatus.PENDING
    verification_date: Optional[datetime] = None
    verification_notes: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "id": "DOC12345",
                "student_id": "S12345",
                "admission_id": "ADM12345",
                "document_type": "transcript",
                "file_name": "academic_transcript.pdf",
                "file_path": "/uploads/S12345/academic_transcript.pdf",
                "uploaded_date": "2025-01-15T12:00:00",
                "verification_status": "pending",
                "verification_date": None,
                "verification_notes": None
            }
        }

class DocumentUpdate(BaseModel):
    verification_status: Optional[VerificationStatus] = None
    verification_date: Optional[datetime] = None
    verification_notes: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "verification_status": "verified",
                "verification_date": "2025-01-16T10:30:00",
                "verification_notes": "All information verified successfully"
            }
        }

class DocumentQuery(BaseModel):
    student_id: Optional[str] = None
    admission_id: Optional[str] = None
    document_type: Optional[DocumentType] = None
    verification_status: Optional[VerificationStatus] = None