# backend/routers/admissions.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from ..models.admission import Admission, AdmissionCreate, AdmissionUpdate, AdmissionStatus
from ..models.student import Student
from ..database.chroma_client import get_client
from ..Agents.admission_officer import AdmissionOfficerAgent
from ..Agents.shortlisting_agent import ShortlistingAgent

router = APIRouter()

@router.post("/", response_model=Admission, status_code=status.HTTP_201_CREATED)
async def create_admission(admission: AdmissionCreate, db=Depends(get_client)):
    """Submit a new admission application"""
    # Check if student exists
    student = await db.get_student(admission.student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student not found"
        )
    
    # Check if admission already exists
    existing_admission = await db.get_admission_by_student_and_program(
        admission.student_id, admission.program
    )
    if existing_admission:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admission application already exists for this student and program"
        )
    
    # Create admission with initial status
    admission.status = AdmissionStatus.SUBMITTED
    return await db.create_admission(admission)

@router.get("/{admission_id}", response_model=Admission)
async def get_admission(admission_id: str, db=Depends(get_client)):
    """Get admission details by ID"""
    admission = await db.get_admission(admission_id)
    if not admission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admission not found"
        )
    return admission

@router.put("/{admission_id}", response_model=Admission)
async def update_admission(admission_id: str, admission_update: AdmissionUpdate, db=Depends(get_client)):
    """Update admission details"""
    existing_admission = await db.get_admission(admission_id)
    if not existing_admission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admission not found"
        )
    
    updated_admission = await db.update_admission(admission_id, admission_update)
    return updated_admission

@router.delete("/{admission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_admission(admission_id: str, db=Depends(get_client)):
    """Delete an admission application"""
    existing_admission = await db.get_admission(admission_id)
    if not existing_admission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admission not found"
        )
    
    await db.delete_admission(admission_id)
    return None

@router.get("/", response_model=List[Admission])
async def list_admissions(
    student_id: Optional[str] = None,
    program: Optional[str] = None,
    status: Optional[AdmissionStatus] = None,
    skip: int = 0,
    limit: int = 100,
    db=Depends(get_client)
):
    """List all admissions with optional filters"""
    admissions = await db.list_admissions(
        student_id=student_id, 
        program=program, 
        status=status, 
        skip=skip, 
        limit=limit
    )
    return admissions

@router.post("/{admission_id}/evaluate", response_model=Admission)
async def evaluate_admission(admission_id: str, db=Depends(get_client)):
    """Evaluate an admission application using the admission officer agent"""
    admission = await db.get_admission(admission_id)
    if not admission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admission not found"
        )
    
    # Check if admission is in a state that can be evaluated
    if admission.status not in [AdmissionStatus.SUBMITTED, AdmissionStatus.UNDER_REVIEW]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Admission cannot be evaluated in '{admission.status}' status"
        )
    
    # Get student details
    student = await db.get_student(admission.student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    # Get documents
    documents = await db.get_student_documents(admission.student_id)
    
    # Use admission officer agent to evaluate
    officer = AdmissionOfficerAgent()
    evaluation_result = await officer.evaluate_application(admission, student, documents)
    
    # Update admission with evaluation result
    admission_update = AdmissionUpdate(
        status=evaluation_result["status"],
        evaluation_notes=evaluation_result["notes"]
    )
    
    updated_admission = await db.update_admission(admission_id, admission_update)
    return updated_admission

@router.post("/shortlist", response_model=List[Student])
async def shortlist_applicants(
    program: str,
    limit: int = 10,
    db=Depends(get_client)
):
    """Shortlist top applicants for a program using the shortlisting agent"""
    # Get all applications for the program with status UNDER_REVIEW
    admissions = await db.list_admissions(
        program=program,
        status=AdmissionStatus.UNDER_REVIEW
    )
    
    if not admissions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No applications found for program '{program}' with status UNDER_REVIEW"
        )
    
    # Get student details for each admission
    students = []
    for admission in admissions:
        student = await db.get_student(admission.student_id)
        if student:
            students.append(student)
    
    # Use shortlisting agent to shortlist
    shortlister = ShortlistingAgent()
    shortlisted_students = await shortlister.shortlist(students, program, limit)
    
    return shortlisted_students