from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

class LoanStatus(str, Enum):
    APPLIED = "applied"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    DISBURSED = "disbursed"

class LoanCreate(BaseModel):
    student_id: str
    admission_id: str
    amount: float
    purpose: str
    requested_date: datetime = Field(default_factory=datetime.now)
    
    class Config:
        schema_extra = {
            "example": {
                "student_id": "S12345",
                "admission_id": "ADM12345",
                "amount": 10000.00,
                "purpose": "Tuition fees",
                "requested_date": "2025-01-15T12:00:00"
            }
        }

class Loan(LoanCreate):
    id: str
    status: LoanStatus = LoanStatus.APPLIED
    review_date: Optional[datetime] = None
    approval_date: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    disbursement_date: Optional[datetime] = None
    interest_rate: Optional[float] = None
    repayment_terms: Optional[dict] = None
    
    class Config:
        schema_extra = {
            "example": {
                "id": "LOAN12345",
                "student_id": "S12345",
                "admission_id": "ADM12345",
                "amount": 10000.00,
                "purpose": "Tuition fees",
                "requested_date": "2025-01-15T12:00:00",
                "status": "applied",
                "review_date": None,
                "approval_date": None,
                "rejection_reason": None,
                "disbursement_date": None,
                "interest_rate": None,
                "repayment_terms": None
            }
        }

class LoanUpdate(BaseModel):
    status: Optional[LoanStatus] = None
    review_date: Optional[datetime] = None
    approval_date: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    disbursement_date: Optional[datetime] = None
    interest_rate: Optional[float] = None
    repayment_terms: Optional[dict] = None
    
    class Config:
        schema_extra = {
            "example": {
                "status": "approved",
                "approval_date": "2025-01-20T14:30:00",
                "interest_rate": 5.0,
                "repayment_terms": {
                    "duration_months": 36,
                    "monthly_payment": 299.71
                }
            }
        }

class LoanQuery(BaseModel):
    student_id: Optional[str] = None
    admission_id: Optional[str] = None
    status: Optional[LoanStatus] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None