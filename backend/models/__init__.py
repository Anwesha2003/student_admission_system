# backend/models/__init__.py
from student_admission_system.backend.models.admission import AdmissionStatus, Admission, AdmissionCreate, AdmissionUpdate, AdmissionQuery
from student_admission_system.backend.models.document import Document, DocumentType,DocumentUpdate, DocumentQuery
from student_admission_system.backend.models.loan import LoanStatus, LoanCreate, Loan, LoanUpdate, LoanQuery
from student_admission_system.backend.models.student import StudentCreate, Student, StudentUpdate, StudentQuery

__all__ = [
    "AdmissionStatus", "Admission", "AdmissionCreate", "AdmissionUpdate", "AdmissionQuery",
    "Document", "DocumentType", "DocumentUpdate", "DocumentQuery",
    "LoanStatus", "LoanCreate", "Loan", "LoanUpdate", "LoanQuery",
    "StudentCreate", "Student", "StudentUpdate", "StudentQuery"
]