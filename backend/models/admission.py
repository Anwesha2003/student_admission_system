from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

class AdmissionStatus(str, Enum):
    PENDING = "pending"
    DOCUMENT_VERIFICATION = "document_verification"
    SHORTLISTED = "shortlisted"
    REJECTED = "rejected"
    ACCEPTED = "accepted"
    ENROLLED = "enrolled"

class AdmissionCreate(BaseModel):
    student_id: str
    program: str
    application_date: datetime = Field(default_factory=datetime.now)
    status: AdmissionStatus = AdmissionStatus.PENDING
    
    class Config:
        schema_extra = {
            "example": {
                "student_id": "S12345",
                "program": "Computer Science",
                "application_date": "2025-01-15T12:00:00",
                "status": "pending"
            }
        }

class Admission(AdmissionCreate):
    id: str
    documents_submitted: List[str] = []
    verification_results: Optional[dict] = None
    shortlisting_results: Optional[dict] = None
    admission_letter_sent: bool = False
    fee_slip_sent: bool = False
    communication_history: List[dict] = []
    
    class Config:
        schema_extra = {
            "example": {
                "id": "ADM12345",
                "student_id": "S12345",
                "program": "Computer Science",
                "application_date": "2025-01-15T12:00:00",
                "status": "pending",
                "documents_submitted": ["transcript", "recommendation_letter"],
                "verification_results": {"transcript": "verified", "recommendation_letter": "pending"},
                "shortlisting_results": None,
                "admission_letter_sent": False,
                "fee_slip_sent": False,
                "communication_history": [{
                    "date": "2025-01-16T10:30:00",
                    "message": "Application received",
                    "sender": "system"
                }]
            }
        }

class AdmissionUpdate(BaseModel):
    status: Optional[AdmissionStatus] = None
    verification_results: Optional[dict] = None
    shortlisting_results: Optional[dict] = None
    admission_letter_sent: Optional[bool] = None
    fee_slip_sent: Optional[bool] = None
    
    class Config:
        schema_extra = {
            "example": {
                "status": "document_verification",
                "verification_results": {"transcript": "verified", "recommendation_letter": "pending"}
            }
        }

class AdmissionQuery(BaseModel):
    student_id: Optional[str] = None
    program: Optional[str] = None
    status: Optional[AdmissionStatus] = None
    application_date_start: Optional[datetime] = None
    application_date_end: Optional[datetime] = None