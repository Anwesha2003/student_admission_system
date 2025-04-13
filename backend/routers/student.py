# backend/routers/students.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from ..models.student import Student, StudentCreate, StudentUpdate
from backend.database.chroma_client import get_client
from ..Agents.student_counsellor import StudentCounsellorAgent

router = APIRouter()

@router.post("/", response_model=Student, status_code=status.HTTP_201_CREATED)
async def create_student(student: StudentCreate, db=Depends(get_client)):
    """Create a new student profile"""
    # Check if student with same email already exists
    existing_student = await db.get_student_by_email(student.email)
    if existing_student:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student with this email already exists"
        )
    
    return await db.create_student(student)

@router.get("/{student_id}", response_model=Student)
async def get_student(student_id: str, db=Depends(get_client)):
    """Get student details by ID"""
    student = await db.get_student(student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    return student

@router.put("/{student_id}", response_model=Student)
async def update_student(student_id: str, student_update: StudentUpdate, db=Depends(get_client)):
    """Update student details"""
    existing_student = await db.get_student(student_id)
    if not existing_student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    updated_student = await db.update_student(student_id, student_update)
    return updated_student

@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_student(student_id: str, db=Depends(get_client)):
    """Delete a student profile"""
    existing_student = await db.get_student(student_id)
    if not existing_student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    await db.delete_student(student_id)
    return None

@router.get("/", response_model=List[Student])
async def list_students(
    name: Optional[str] = None,
    email: Optional[str] = None,
    program: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db=Depends(get_client)
):
    """List all students with optional filters"""
    students = await db.list_students(name=name, email=email, program=program, skip=skip, limit=limit)
    return students

@router.post("/{student_id}/counselling", status_code=status.HTTP_200_OK)
async def get_counselling(student_id: str, query: str, db=Depends(get_client)):
    """Get counselling advice for a student"""
    student = await db.get_student(student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    counsellor = StudentCounsellorAgent()
    advice = await counsellor.provide_advice(student, query)
    
    return {"advice": advice}