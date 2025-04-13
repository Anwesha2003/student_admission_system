# config/__init__.py
from .settings import (
    APP_NAME,
    DATABASE_URL,
    API_BASE_URL,
    SECRET_KEY,
    DEBUG_MODE,
    ALLOWED_DOCUMENT_TYPES,
    MAX_UPLOAD_SIZE,
    ADMIN_EMAIL
)

__all__ = [
    "APP_NAME",
    "DATABASE_URL",
    "API_BASE_URL",
    "SECRET_KEY",
    "DEBUG_MODE",
    "ALLOWED_DOCUMENT_TYPES",
    "MAX_UPLOAD_SIZE",
    "ADMIN_EMAIL"
]