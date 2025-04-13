# frontend/pages/__init__.py
"""
University Portal Pages Package

This package contains all the streamlit pages for the University Portal application.
Pages include:
- Admin Dashboard: For administrators to view application metrics and AI agent performance
- Admission Form: For students to submit applications and for admins to review them
- Document Upload: For document submission and verification
- Loan Application: For financial aid applications and processing
"""

from typing import Dict, List, Any, Callable
import streamlit as st
import pandas as pd
from datetime import datetime

# Import components from other modules if necessary
from components.sidebar import render_sidebar
from components.header import render_header
from components.footer import render_footer
from components.login import initialize_auth_db, hash_password, authenticate_user, register_user, create_seed_users, login_page, add_logout_to_sidebar, student_dashboard, admin_dashboard, main
from admission_form import get_student_application, save_application, get_all_applications, update_application_status
from document_upload import get_documents_for_student, update_document_status
from loan_application import load_loan_application, save_loan_application, update_loan_status, load_all_loan_applications, load_financial_aid_options

__all__ = ["st", "pd", "datetime", "render_sidebar", "render_header", "render_footer","initialize_auth_db", "hash_password", "authenticate_user", "register_user", "create_seed_users","login_page", "add_logout_to_sidebar","student_dashboard", "admin_dashboard", "main","get_student_application", "save_application", "get_all_applications", "update_application_status","get_documents_for_student","update_document_status",
           "load_loan_application"," save_loan_application"," update_loan_status","load_all_loan_applications", "load_financial_aid_options"]