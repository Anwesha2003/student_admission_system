# config/settings.py
import os
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Dict, Any

# Load environment variables from .env file if it exists
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Application settings
APP_NAME = "University Admission System"
DEBUG_MODE = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
SECRET_KEY = os.getenv("SECRET_KEY", "hBBDoRQsTkThSxLyFqFDIqM7cBEkyqJFqed_6ydc_lE")
API_VERSION = "v1"

# API settings
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:8501")

# Database settings
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./admission_system.db")
CHROMA_PERSISTENCE_DIR = os.getenv("CHROMA_PERSISTENCE_DIR", "./chroma_db")

# Document settings
ALLOWED_DOCUMENT_TYPES = [
    "application/pdf",
    "image/jpeg",
    "image/png",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
]
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB in bytes

# Email configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "anweshadas23122003@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "anwesha#2003")
EMAIL_FROM = os.getenv("EMAIL_FROM", "noreply@university.edu")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@university.edu")

# AI Model settings
AI_MODEL = os.getenv("AI_MODEL", "gpt-4o")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "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")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "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")

# Admission settings
ADMISSION_CYCLES = {
    "Fall 2025": {
        "start_date": "2024-09-01",
        "end_date": "2025-03-31",
        "decision_date": "2025-05-15"
    },
    "Spring 2026": {
        "start_date": "2025-03-01",
        "end_date": "2025-09-30",
        "decision_date": "2025-11-15"
    }
}

# Required documents by program
REQUIRED_DOCUMENTS: Dict[str, List[str]] = {
    "default": ["transcripts", "recommendation_letters", "statement_of_purpose", "resume"],
    "MBA": ["transcripts", "recommendation_letters", "statement_of_purpose", "resume", "gmat_scores"],
    "Engineering": ["transcripts", "recommendation_letters", "statement_of_purpose", "resume", "gre_scores"],
    "Medicine": ["transcripts", "recommendation_letters", "statement_of_purpose", "resume", "mcat_scores", "medical_clearance"],
    "Law": ["transcripts", "recommendation_letters", "statement_of_purpose", "resume", "lsat_scores"]
}

# Loan settings
LOAN_INTEREST_RATES = {
    "federal": 4.99,
    "private": 6.75,
    "university": 3.5
}
MAX_LOAN_AMOUNT = 50000

# Auth settings
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Logging configuration
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "standard",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "standard",
            "filename": os.path.join(BASE_DIR, "logs", "application.log"),
            "maxBytes": 10485760,  # 10 MB
            "backupCount": 10,
        },
    },
    "loggers": {
        "": {
            "handlers": ["console", "file"],
            "level": "INFO",
        }
    }
}