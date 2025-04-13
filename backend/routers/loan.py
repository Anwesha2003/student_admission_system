# backend/routers/loans.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from ..models.loan import Loan, LoanCreate, LoanUpdate, LoanStatus
from ..database.chroma_client import get_db
from ..agents.loan_agent import LoanAgent

router = APIRouter()

@router.post("/", response_model=Loan, status_code=status.HTTP_201_CREATED)
async def create_loan(loan: LoanCreate, db=Depends(get_db)):
    """Submit a new loan application"""
    # Check if student exists
    student = await db.get_student(loan.student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student not found"
        )
    
    # Check if admission exists and is approved
    admission = await db.get_admission(loan.admission_id)
    if not admission:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admission not found"
        )
    
    if admission.student_id != loan.student_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admission does not belong to this student"
        )
    
    # Create loan with initial status
    loan.status = LoanStatus.SUBMITTED
    return await db.create_loan(loan)

@router.get("/{loan_id}", response_model=Loan)
async def get_loan(loan_id: str, db=Depends(get_db)):
    """Get loan details by ID"""
    loan = await db.get_loan(loan_id)
    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loan not found"
        )
    return loan

@router.put("/{loan_id}", response_model=Loan)
async def update_loan(loan_id: str, loan_update: LoanUpdate, db=Depends(get_db)):
    """Update loan details"""
    existing_loan = await db.get_loan(loan_id)
    if not existing_loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loan not found"
        )
    
    updated_loan = await db.update_loan(loan_id, loan_update)
    return updated_loan

@router.delete("/{loan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_loan(loan_id: str, db=Depends(get_db)):
    """Delete a loan application"""
    existing_loan = await db.get_loan(loan_id)
    if not existing_loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loan not found"
        )
    
    await db.delete_loan(loan_id)
    return None

@router.get("/", response_model=List[Loan])
async def list_loans(
    student_id: Optional[str] = None,
    admission_id: Optional[str] = None,
    status: Optional[LoanStatus] = None,
    skip: int = 0,
    limit: int = 100,
    db=Depends(get_db)
):
    """List all loans with optional filters"""
    loans = await db.list_loans(
        student_id=student_id,
        admission_id=admission_id,
        status=status,
        skip=skip,
        limit=limit
    )
    return loans

@router.post("/{loan_id}/evaluate", response_model=Loan)
async def evaluate_loan(loan_id: str, db=Depends(get_db)):
    """Evaluate a loan application using the loan agent"""
    loan = await db.get_loan(loan_id)
    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loan not found"
        )
    
    # Check if loan is in a state that can be evaluated
    if loan.status not in [LoanStatus.SUBMITTED, LoanStatus.UNDER_REVIEW]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Loan cannot be evaluated in '{loan.status}' status"
        )
    
    # Get student details
    student = await db.get_student(loan.student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    # Get admission details
    admission = await db.get_admission(loan.admission_id)
    if not admission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admission not found"
        )
    
    # Use loan agent to evaluate
    agent = LoanAgent()
    evaluation_result = await agent.evaluate_loan(loan, student, admission)
    
    # Update loan with evaluation result
    loan_update = LoanUpdate(
        status=evaluation_result["status"],
        approved_amount=evaluation_result.get("approved_amount"),
        interest_rate=evaluation_result.get("interest_rate"),
        evaluation_notes=evaluation_result["notes"]
    )
    
    updated_loan = await db.update_loan(loan_id, loan_update)
    return updated_loan

@router.post("/{loan_id}/recommendation", status_code=status.HTTP_200_OK)
async def get_loan_recommendation(loan_id: str, db=Depends(get_db)):
    """Get loan recommendation for a student"""
    loan = await db.get_loan(loan_id)
    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loan not found"
        )
    
    # Get student details
    student = await db.get_student(loan.student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    # Get admission details
    admission = await db.get_admission(loan.admission_id)
    if not admission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admission not found"
        )
    
    # Use loan agent to get recommendation
    agent = LoanAgent()
    recommendation = await agent.get_recommendation(loan, student, admission)
    
    return {"recommendation": recommendation}