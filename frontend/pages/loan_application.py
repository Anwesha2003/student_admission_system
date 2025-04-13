import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json
import uuid
from datetime import datetime

from components.sidebar import render_sidebar
from components.header import render_header
from components.footer import render_footer
from backend.database import chroma_client as db

# Render sidebar for navigation
render_sidebar()

# Render header
render_header("Financial Aid & Loan Application", "Explore financial options for your education")

# Check if user is logged in and their role
user_role = st.session_state.get("user_role")

# Initialize database if not already done
if "db_initialized" not in st.session_state:
    db.initialize_chroma_db()
    st.session_state.db_initialized = True

def load_loan_application(student_id):
    """Load loan application for a specific student"""
    loan_applications = db.query_documents(
        collection_name="loans",
        query="",  # Empty query to match all documents
        metadata_filter={"student_id": student_id}
    )
    if loan_applications:
        return loan_applications[0]  # Return the first matching application
    return None

def save_loan_application(loan_data):
    """Save loan application to database"""
    # Generate unique ID if not provided
    if "document_id" not in loan_data:
        loan_data["document_id"] = f"L{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6]}"
    
    # Add submission timestamp
    if "submitted_date" not in loan_data:
        loan_data["submitted_date"] = datetime.now().strftime("%Y-%m-%d")
    
    # Set initial status if not provided
    if "status" not in loan_data:
        loan_data["status"] = "Pending"
    
    # Save to database
    db.add_document(
        collection_name="loans",
        document=loan_data,
        document_id=loan_data["document_id"],
        metadata={
            "student_id": loan_data["student_id"],
            "status": loan_data["status"],
            "loan_type": loan_data["loan_type"],
            "amount": loan_data["loan_amount"]
        }
    )
    return loan_data["document_id"]

def update_loan_status(document_id, new_status):
    """Update the status of a loan application"""
    loan_data = db.get_document("loans", document_id)
    if loan_data:
        loan_data["status"] = new_status
        db.update_document(
            collection_name="loans",
            document_id=document_id,
            document=loan_data,
            metadata={
                "student_id": loan_data["student_id"],
                "status": new_status,
                "loan_type": loan_data["loan_type"],
                "amount": loan_data["loan_amount"]
            }
        )
        return True
    return False

def load_all_loan_applications(status_filter=None, loan_type_filter=None, min_amount=0, max_amount=100000):
    """Load all loan applications with optional filters"""
    metadata_filter = {}
    
    if status_filter and status_filter != "All":
        metadata_filter["status"] = status_filter
    
    if loan_type_filter and loan_type_filter != "All":
        metadata_filter["loan_type"] = loan_type_filter
    
    # Note: ChromaDB doesn't support range queries directly, so we'll filter by amount after retrieval
    
    # Query with any applicable filters
    loan_applications = db.query_documents(
        collection_name="loans",
        query="",  # Empty query to match all documents
        n_results=100,  # Adjust as needed
        metadata_filter=metadata_filter if metadata_filter else None
    )
    
    # Apply amount filter manually
    if loan_applications:
        filtered_applications = [
            app for app in loan_applications 
            if min_amount <= app.get("loan_amount", 0) <= max_amount
        ]
        return filtered_applications
    
    return []

def load_financial_aid_options():
    """Load financial aid options from database"""
    return db.query_documents(
        collection_name="eligibility_criteria",
        query="financial aid",
        n_results=10
    )

if user_role == "student":
    # Student view - Loan application interface
    student_id = st.session_state.get("student_id")
    
    # Financial aid information
    financial_aid_options = load_financial_aid_options()
    
    # If no options found in DB, show default info
    if not financial_aid_options:
        st.info("""
        **Financial Aid Options:**
        - University Scholarships: Merit-based awards up to 50% of tuition
        - Student Loans: Low-interest education loans with flexible repayment options
        - Work-Study Programs: On-campus employment opportunities to help with expenses
        - External Scholarships: Information about partner organizations offering additional aid
        """)
    else:
        # Display options from database
        st.subheader("Financial Aid Options")
        for option in financial_aid_options:
            st.info(f"**{option.get('program', '')}:** {option.get('additional_requirements', '')}")
    
    # Check if student has an existing loan application
    existing_loan = load_loan_application(student_id)
    
    if existing_loan:
        # Display loan application status
        st.success("Your loan application has been submitted successfully!")
        
        # Loan application details from database
        st.subheader("Loan Application Details")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**Application ID:** {existing_loan.get('document_id', 'N/A')}")
            st.markdown(f"**Date Submitted:** {existing_loan.get('submitted_date', 'N/A')}")
            st.markdown(f"**Status:** {existing_loan.get('status', 'Pending')}")
            st.markdown(f"**Amount Requested:** ${existing_loan.get('loan_amount', 0):,.2f}")
        
        with col2:
            st.markdown(f"**Loan Term:** {existing_loan.get('loan_term', 'N/A')} years")
            
            # Calculate monthly payment
            if 'loan_amount' in existing_loan and 'loan_term' in existing_loan:
                interest_rate = existing_loan.get('interest_rate', 4.5) / 100
                monthly_rate = interest_rate / 12
                loan_term_months = existing_loan['loan_term'] * 12
                
                monthly_payment = existing_loan['loan_amount'] * (monthly_rate * (1 + monthly_rate) ** loan_term_months) / ((1 + monthly_rate) ** loan_term_months - 1)
                st.markdown(f"**Estimated Monthly Payment:** ${monthly_payment:.2f}")
                
            st.markdown(f"**Interest Rate:** {existing_loan.get('interest_rate', 4.5)}%")
        
        # Display next steps
        st.subheader("Next Steps")
        documents_pending = existing_loan.get('documents_pending', [])
        if documents_pending:
            for doc in documents_pending:
                st.warning(f"• Upload required document: {doc}")
        else:
            st.info("All required documents have been submitted.")
        
        st.markdown(existing_loan.get("next_steps", "Your application is being processed."))
        
    else:
        # New loan application form
        tab1, tab2 = st.tabs(["Apply for Loan", "Loan Calculator"])
        
        with tab1:
            st.subheader("Student Loan Application")
            
            loan_type = st.selectbox("Loan Type", ["Federal Student Loan", "University Financial Aid", "Private Education Loan"])
            
            col1, col2 = st.columns(2)
            with col1:
                loan_amount = st.number_input("Loan Amount ($)", min_value=1000, max_value=100000, value=15000, step=1000)
                loan_purpose = st.multiselect("Loan Purpose", ["Tuition", "Books and Supplies", "Housing", "Food", "Transportation", "Other Expenses"])
            
            with col2:
                loan_term = st.slider("Loan Term (Years)", min_value=5, max_value=25, value=10, step=5)
                cosigner = st.radio("Will you have a cosigner?", ["Yes", "No"])
            
            st.subheader("Financial Information")
            
            col1, col2 = st.columns(2)
            with col1:
                annual_income = st.number_input("Annual Income ($)", min_value=0, max_value=200000, value=0)
                employment_status = st.selectbox("Employment Status", ["Unemployed", "Part-time", "Full-time", "Self-employed"])
                
            with col2:
                other_aid = st.number_input("Other Financial Aid/Scholarships ($)", min_value=0, max_value=100000, value=0)
                existing_debt = st.number_input("Existing Debt ($)", min_value=0, max_value=200000, value=0)
            
            st.subheader("Required Documents")
            st.info("You will need to upload these documents after submitting your application")
            st.markdown("""
            - Proof of Identity
            - Proof of Income (if applicable)
            - Credit History
            - Cosigner Information (if applicable)
            """)
            
            agree = st.checkbox("I certify that all information provided is true and complete to the best of my knowledge")
            understand = st.checkbox("I understand that submitting this application does not guarantee loan approval")
            
            if st.button("Submit Loan Application", disabled=not (agree and understand)):
                if not loan_purpose:
                    st.error("Please select at least one loan purpose")
                else:
                    # Create loan application data
                    loan_data = {
                        "student_id": student_id,
                        "loan_type": loan_type,
                        "loan_amount": loan_amount,
                        "loan_purpose": loan_purpose,
                        "loan_term": loan_term,
                        "cosigner": cosigner,
                        "annual_income": annual_income,
                        "employment_status": employment_status,
                        "other_aid": other_aid,
                        "existing_debt": existing_debt,
                        "interest_rate": 4.5,  # Default interest rate
                        "status": "Under Review",
                        "documents_pending": ["Proof of Identity", "Proof of Income", "Credit History"],
                        "next_steps": "Please upload pending documents"
                    }
                    
                    # Save to database
                    document_id = save_loan_application(loan_data)
                    
                    st.success(f"Loan application submitted successfully! Your application ID is {document_id}")
                    st.info("Please proceed to document upload section to complete your application")
                    
                    st.session_state.loan_submitted = True
                    st.rerun()
        
        with tab2:
            st.subheader("Loan Calculator")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                calc_loan_amount = st.number_input("Principal Amount ($)", min_value=1000, max_value=100000, value=15000, step=1000, key="calc_amount")
            
            with col2:
                calc_interest_rate = st.number_input("Annual Interest Rate (%)", min_value=1.0, max_value=15.0, value=4.5, step=0.1)
            
            with col3:
                calc_loan_term = st.number_input("Loan Term (Years)", min_value=5, max_value=25, value=10, step=1, key="calc_term")
            
            if st.button("Calculate"):
                interest_rate_monthly = calc_interest_rate / 100 / 12
                loan_term_months = calc_loan_term * 12
                
                monthly_payment = calc_loan_amount * (interest_rate_monthly * (1 + interest_rate_monthly) ** loan_term_months) / ((1 + interest_rate_monthly) ** loan_term_months - 1)
                
                total_payment = monthly_payment * loan_term_months
                total_interest = total_payment - calc_loan_amount
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Monthly Payment", f"${monthly_payment:.2f}")
                    st.metric("Total Payment", f"${total_payment:.2f}")
                    st.metric("Total Interest", f"${total_interest:.2f}")
                
                with col2:
                    years = range(1, calc_loan_term + 1)
                    remaining_balance = [calc_loan_amount * (1 - ((1 + interest_rate_monthly) ** (year * 12) - 1) / ((1 + interest_rate_monthly) ** loan_term_months - 1)) for year in years]
                    
                    fig, ax = plt.subplots()
                    ax.plot(years, remaining_balance)
                    ax.set_xlabel("Years")
                    ax.set_ylabel("Remaining Balance ($)")
                    ax.set_title("Loan Amortization Schedule")
                    st.pyplot(fig)

elif user_role == "admin":
    st.subheader("Loan Applications Dashboard")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox("Filter by Status", ["All", "Pending", "Under Review", "Approved", "Denied", "Awaiting Documents"])
    with col2:
        loan_type_filter = st.selectbox("Filter by Loan Type", ["All", "Federal Student Loan", "University Financial Aid", "Private Education Loan"])
    with col3:
        amount_filter = st.slider("Amount Range", 0, 100000, (0, 100000))
    
    # Load applications from database with filters
    loan_applications = load_all_loan_applications(
        status_filter=status_filter if status_filter != "All" else None,
        loan_type_filter=loan_type_filter if loan_type_filter != "All" else None,
        min_amount=amount_filter[0],
        max_amount=amount_filter[1]
    )
    
    # Convert to dataframe for display
    if loan_applications:
        # Extract relevant fields for the table
        table_data = []
        for app in loan_applications:
            table_data.append({
                "id": app.get("document_id", ""),
                "student_id": app.get("student_id", ""),
                "type": app.get("loan_type", ""),
                "amount": app.get("loan_amount", 0),
                "date": app.get("submitted_date", ""),
                "status": app.get("status", "")
            })
        
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No loan applications found matching the selected filters.")
    
    st.subheader("Loan Application Details")
    
    # Create list of applications for selection dropdown
    app_options = []
    if loan_applications:
        app_options = [f"{app.get('document_id', '')} - {app.get('student_id', '')} (${app.get('loan_amount', 0):,.2f})" for app in loan_applications]
    
    selected_loan = st.selectbox("Select Application to Review", app_options if app_options else ["No applications available"])
    
    if selected_loan and "No applications" not in selected_loan:
        loan_id = selected_loan.split(" - ")[0]
        
        # Fetch detailed loan data
        loan_detail = db.get_document("loans", loan_id)
        
        if loan_detail:
            col1, col2 = st.columns(2)
            
            with col1:
                # Format loan data for display
                display_data = {
                    "document_id": loan_detail.get("document_id", ""),
                    "student_info": {
                        "student_id": loan_detail.get("student_id", ""),
                        "academic_standing": "Good"  # Could retrieve from students collection
                    },
                    "loan_details": {
                        "amount": loan_detail.get("loan_amount", 0),
                        "type": loan_detail.get("loan_type", ""),
                        "purpose": loan_detail.get("loan_purpose", []),
                        "term": f"{loan_detail.get('loan_term', 10)} years",
                        "interest_rate": f"{loan_detail.get('interest_rate', 4.5)}%"
                    },
                    "financial_info": {
                        "annual_income": loan_detail.get("annual_income", 0),
                        "other_aid": loan_detail.get("other_aid", 0),
                        "existing_debt": loan_detail.get("existing_debt", 0)
                    },
                    "documents": {
                        status: "Pending" for status in loan_detail.get("documents_pending", [])
                    }
                }
                
                st.json(display_data)
            
            with col2:
                st.subheader("AI Risk Assessment")
                
                # Calculate risk score (simple example)
                income = loan_detail.get("annual_income", 0)
                loan_amount = loan_detail.get("loan_amount", 0)
                existing_debt = loan_detail.get("existing_debt", 0)
                
                # Simple risk score calculation (would be more sophisticated in production)
                if income > 0:
                    debt_ratio = (loan_amount + existing_debt) / income
                    risk_score = max(0, min(100, 100 - (debt_ratio * 20)))
                else:
                    risk_score = 50  # Default moderate risk for no income
                
                st.progress(risk_score/100)
                
                risk_level = "High Risk"
                if risk_score >= 70:
                    risk_level = "Low Risk"
                elif risk_score >= 40:
                    risk_level = "Moderate Risk"
                    
                st.markdown(f"**Risk Score:** {risk_score:.0f}/100 ({risk_level})")
                
                # Analysis based on risk score
                analysis = []
                if risk_score >= 70:
                    analysis = [
                        "Strong financial position",
                        "Good debt-to-income ratio",
                        "Loan amount appropriate for circumstances"
                    ]
                elif risk_score >= 40:
                    analysis = [
                        "Acceptable financial position",
                        "Moderate debt-to-income ratio",
                        "Consider reduced loan amount"
                    ]
                else:
                    analysis = [
                        "Weak financial position",
                        "High debt-to-income ratio",
                        "Loan amount may be too high"
                    ]
                
                st.markdown("**Analysis:**")
                for point in analysis:
                    st.markdown(f"- {point}")
                
                recommendation = "Deny" if risk_score < 40 else "Approve with conditions" if risk_score < 70 else "Approve with standard terms"
                st.markdown(f"**Recommendation:** {recommendation}")
            
            col1, col2, col3 = st.columns(3)
            current_status = loan_detail.get("status", "")
            
            with col1:
                if st.button("Approve Loan", use_container_width=True):
                    if update_loan_status(loan_id, "Approved"):
                        st.success(f"Loan {loan_id} has been approved")
                        st.rerun()
            
            with col2:
                if st.button("Request Documents", use_container_width=True):
                    if update_loan_status(loan_id, "Awaiting Documents"):
                        st.info(f"Document request sent to student")
                        st.rerun()
            
            with col3:
                if st.button("Deny Loan", use_container_width=True):
                    denial_reason = st.text_area("Denial Reason", height=100)
                    if st.button("Confirm Denial"):
                        # Update loan status and add denial reason
                        loan_detail["status"] = "Denied"
                        loan_detail["denial_reason"] = denial_reason
                        db.update_document(
                            collection_name="loans",
                            document_id=loan_id,
                            document=loan_detail,
                            metadata={
                                "student_id": loan_detail["student_id"],
                                "status": "Denied",
                                "loan_type": loan_detail["loan_type"],
                                "amount": loan_detail["loan_amount"]
                            }
                        )
                        st.error(f"Loan {loan_id} has been denied")
                        st.rerun()

else:
    st.warning("Please log in to apply for financial aid or view your loan status")

render_footer()