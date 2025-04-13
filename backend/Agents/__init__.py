# backend/agents/__init__.py
from .admission_officer import AdmissionOfficerAgent
from .document_checker import DocumentCheckerAgent
from .shortlisting_agent import ShortlistingAgent
from .student_counsellor import StudentCounsellorAgent
from .loan_agent import LoanAgent

__all__ = [
    "AdmissionOfficerAgent",
    "DocumentCheckerAgent",
    "ShortlistingAgent",
    "StudentCounsellorAgent",
    "LoanAgent"
]