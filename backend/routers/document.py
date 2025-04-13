from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import List, Optional
import logging

from ..database.chroma_client import ChromaClient
from ..models.student import Student, StudentStatus
from ..utils.helpers import generate_id, validate_email, sanitize_input

router = APIRouter()
logger = logging.getLogger(__name__)

async def get_db():
    db_client = ChromaClient()
    return db_client

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_student(student: Student, db: ChromaClient = Depends(get_db)):
    if not student.id:
        student.id = generate_id("STD")
    
    if not validate_email(student.contact.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format"
        )
    
    existing_student = await db.get_student(student.id)
    if existing_student and existing_student['ids']:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Student with ID {student.id} already exists"
        )
    
    student_data = student.dict()
    student_metadata = {
        "full_name": student.full_name(),
        "email": student.contact.email,
        "status": student.status
    }
    
    await db.add_student(student.id, student_data, student_metadata)
    logger.info(f"Created student: {student.id}")
    
    return {"id": student.id, "message": "Student created successfully"}

@router.get("/{student_id}")
async def get_student(student_id: str, db: ChromaClient = Depends(get_db)):
    student = await db.get_student(student_id)
    
    if not student or not student['ids']:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {student_id} not found"
        )
    
    return student

@router.get("/")
async def list_students(
    status: Optional[StudentStatus] = None,
    search: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100),
    db: ChromaClient = Depends(get_db)
):
    if search:
        sanitized_search = sanitize_input(search)
        results = await db.search_students(sanitized_search, n_results=limit)
    else:
        results = await db.search_students("", n_results=limit)
    
    students = results['documents']
    
    if status:
        students = [s for s in students if s.get('status') == status]
    
    return students[:limit]

@router.put("/{student_id}")
async def update_student(
    student_id: str,
    student_update: Student,
    db: ChromaClient = Depends(get_db)
):
    existing_student = await db.get_student(student_id)
    
    if not existing_student or not existing_student['ids']:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {student_id} not found"
        )
    
    student_data = student_update.dict()
    student_metadata = {
        "full_name": student_update.full_name(),
        "email": student_update.contact.email,
        "status": student_update.status
    }
    
    await db.update_student(student_id, student_data, student_metadata)
    logger.info(f"Updated student: {student_id}")
    
    return {"id": student_id, "message": "Student updated successfully"}

@router.delete("/{student_id}")
async def delete_student(student_id: str, db: ChromaClient = Depends(get_db)):
    existing_student = await db.get_student(student_id)
    
    if not existing_student or not existing_student['ids']:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {student_id} not found"
        )
    
    await db.delete_student(student_id)
    logger.info(f"Deleted student: {student_id}")
    
    return {"id": student_id, "message": "Student deleted successfully"}