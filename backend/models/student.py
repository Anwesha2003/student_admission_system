from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class StudentCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str
    date_of_birth: datetime
    address: str
    previous_education: Dict[str, Any]
    gpa: float
    
    class Config:
        schema_extra = {
            "example": {
                "name": "John Doe",
                "email": "john.doe@example.com",
                "phone": "123-456-7890",
                "date_of_birth": "2000-01-01T00:00:00",
                "address": "123 Main St, Anytown, USA",
                "previous_education": {
                    "institution": "High School XYZ",
                    "degree": "High School Diploma",
                    "graduation_date": "2024-05-15",
                    "subjects": ["Math", "Physics", "Computer Science"]
                },
                "gpa": 3.8
            }
        }

class Student(StudentCreate):
    id: str
    registration_date: datetime = Field(default_factory=datetime.now)
    admission_ids: List[str] = []
    loan_ids: List[str] = []
    
    class Config:
        schema_extra = {
            "example": {
                "id": "S12345",
                "name": "John Doe",
                "email": "john.doe@example.com",
                "phone": "123-456-7890",
                "date_of_birth": "2000-01-01T00:00:00",
                "address": "123 Main St, Anytown, USA",
                "previous_education": {
                    "institution": "High School XYZ",
                    "degree": "High School Diploma",
                    "graduation_date": "2024-05-15",
                    "subjects": ["Math", "Physics", "Computer Science"]
                },
                "gpa": 3.8,
                "registration_date": "2025-01-15T12:00:00",
                "admission_ids": ["ADM12345"],
                "loan_ids": []
            }
        }

class StudentUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    previous_education: Optional[Dict[str, Any]] = None
    gpa: Optional[float] = None
    
    class Config:
        schema_extra = {
            "example": {
                "email": "new.email@example.com",
                "phone": "987-654-3210"
            }
        }

class StudentQuery(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    gpa_min: Optional[float] = None
    gpa_max: Optional[float] = None