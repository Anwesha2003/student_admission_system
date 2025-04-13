# backend/routers/__init__.py
from .admission import router as admissions_router
from .document import router as documents_router
from .loan import router as loans_router
from .student import router as students_router

__all__ = ["admissions_router", "documents_router", "loans_router", "students_router"]