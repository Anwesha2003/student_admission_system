from typing import Dict, List, Optional
import uuid
import datetime
import re
import json
from ..models.student import Student
from ..models.loan import LoanApplication
from ..models.admission import Application, AdmissionStatus
from ..models.document import Document, DocumentType

def generate_id(prefix: str = "") -> str:
    return f"{prefix}{uuid.uuid4().hex[:16]}"

def calculate_age(date_of_birth):
    today = datetime.date.today()
    return today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))

def get_document_path(student_id: str, document_type: DocumentType, filename: str) -> str:
    sanitized_filename = re.sub(r'[^\w\-_\. ]', '_', filename)
    return f"documents/{student_id}/{document_type.value}/{sanitized_filename}"

def calculate_loan_eligibility_score(application: LoanApplication, student: Student) -> float:
    base_score = 50
    
    if application.credit_score:
        if application.credit_score >= 750:
            base_score += 25
        elif application.credit_score >= 700:
            base_score += 20
        elif application.credit_score >= 650:
            base_score += 15
        elif application.credit_score >= 600:
            base_score += 10
    
    if application.income_verification:
        base_score += 10
    
    if application.cosigner:
        base_score += 15
    
    return min(100, base_score)

def format_currency(amount: float) -> str:
    return f"${amount:,.2f}"

def extract_text_from_pdf(file_path: str) -> str:
    try:
        import PyPDF2
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfFileReader(file)
            text = ""
            for page_num in range(reader.numPages):
                text += reader.getPage(page_num).extractText()
        return text
    except Exception as e:
        return f"Error extracting text: {str(e)}"

def extract_text_from_docx(file_path: str) -> str:
    try:
        import docx
        doc = docx.Document(file_path)
        text = [paragraph.text for paragraph in doc.paragraphs]
        return "\n".join(text)
    except Exception as e:
        return f"Error extracting text: {str(e)}"

def check_document_authenticity(document: Document) -> bool:
    if document.verification_details and "verified" in document.verification_details:
        return document.verification_details["verified"]
    return False

def get_application_status_color(status: AdmissionStatus) -> str:
    status_colors = {
        AdmissionStatus.DRAFT: "gray",
        AdmissionStatus.SUBMITTED: "blue",
        AdmissionStatus.UNDER_REVIEW: "yellow",
        AdmissionStatus.SHORTLISTED: "purple",
        AdmissionStatus.INTERVIEW_SCHEDULED: "teal",
        AdmissionStatus.INTERVIEW_COMPLETED: "indigo",
        AdmissionStatus.ACCEPTED: "green",
        AdmissionStatus.REJECTED: "red",
        AdmissionStatus.WAITLISTED: "orange",
        AdmissionStatus.DEFERRED: "brown",
        AdmissionStatus.ENROLLED: "emerald",
        AdmissionStatus.WITHDRAWN: "slate"
    }
    return status_colors.get(status, "gray")

def validate_email(email: str) -> bool:
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(email_pattern, email))

def sanitize_input(text: str) -> str:
    return re.sub(r"[<>\"'&]", "", text)

def calculate_completion_percentage(application: Application) -> int:
    required_fields = ["student_id", "application_type", "program", "term"]
    
    if not application.is_complete and application.missing_documents:
        return 50
    
    total_fields = len(required_fields)
    completed_fields = sum(1 for field in required_fields if getattr(application, field, None))
    
    return int((completed_fields / total_fields) * 100)

def format_date(date: datetime.datetime) -> str:
    return date.strftime("%B %d, %Y")

def parse_date(date_str: str) -> Optional[datetime.datetime]:
    try:
        return datetime.datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        try:
            return datetime.datetime.strptime(date_str, "%m/%d/%Y")
        except ValueError:
            return None

def convert_bytes_to_readable_size(size_in_bytes: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(size_in_bytes)
    unit_index = 0
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    return f"{size:.2f} {units[unit_index]}"

def serialize_model(model):
    return json.dumps(model.dict())

def deserialize_model(model_class, json_data):
    return model_class(**json.loads(json_data))