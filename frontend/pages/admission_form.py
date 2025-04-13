import streamlit as st
import pandas as pd
from datetime import datetime
import json
import uuid
import os
import asyncio

from components.sidebar import render_sidebar
from components.header import render_header
from components.footer import render_footer
from backend.database.chroma_client import get_collection,initialize_chroma_db, add_document, get_document, query_documents, update_document

# Import the ShortlistingAgent
from backend.Agents.shortlisting_agent import ShortlistingAgent

# Add this line near the top of your files, after importing streamlit
if "user_role" not in st.session_state:
    st.session_state["user_role"] = "admin"  # For testing only

# Function to check if student has an existing application
def get_student_application(student_id):
    """Retrieve application for a student from ChromaDB."""
    admissions_collection = get_collection("admissions")
    results = admissions_collection.get(
        where={"student_id": student_id}
    )
    
    if results and results['documents'] and len(results['documents']) > 0:
        try:
            # Make sure the document is a valid JSON string
            application_data = json.loads(results['documents'][0])
            application_data['id'] = results['ids'][0]
                
            return application_data
        except json.JSONDecodeError:
            # Handle case where document is not a valid JSON string
            print(f"Invalid JSON document for student ID {student_id}")
            return None
            
    return None

# Function to save application to ChromaDB
def save_application(application_data):
    """Save application data to ChromaDB."""
    try:
        # Ensure collection exists
        admissions_collection = get_collection("admissions")
        
        # Generate a unique application ID
        document_id = f"A{datetime.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:8]}"
        application_data["document_id"] = document_id
        
        # Add metadata for efficient querying
        metadata = {
            "student_id": application_data["student_id"],
            "full_name": f"{application_data['first_name']} {application_data['last_name']}",
            "program": application_data["program_applying_for"],
            "status": "Under Review",
            "submission_date": datetime.now().isoformat()
        }
        
        # Add the application to ChromaDB
        add_document(
            "admissions", 
            application_data, 
            document_id, 
            metadata=metadata
        )
        
        return document_id
    except Exception as e:
        st.error(f"Error saving application: {str(e)}")
        return None


# Function to get all applications (for admin view)
def get_all_applications(status_filter="All", program_filter="All", date_filter=None, search_term=None):
    """Retrieve filtered applications from ChromaDB."""
    try:
        # Ensure collection exists
        admissions_collection = get_collection("admissions")
        
        # Build where clause based on filters
        where_clause = {}
        if status_filter != "All":
            where_clause["status"] = status_filter
        if program_filter != "All":
            where_clause["program"] = program_filter
        
        # Get all applications that match the filters
        results = admissions_collection.get(
            where=where_clause if where_clause else None
        )
        
        applications = []
        for i, doc in enumerate(results['documents']):
            if doc:
                app_data = json.loads(doc)
                metadata = results['metadatas'][i] if results['metadatas'] else {}
                
                # Apply date filter if specified
                if date_filter:
                    submission_date = datetime.fromisoformat(metadata.get('submission_date', '2000-01-01')).date()
                    if submission_date < date_filter:
                        continue
                
                # Apply search filter if specified
                if search_term and search_term.lower() not in metadata.get('full_name', '').lower() and search_term not in app_data.get('document_id', ''):
                    continue
                    
                # Add application to results
                applications.append({
                    "id": app_data.get('document_id', results['ids'][i]),
                    "name": metadata.get('full_name', 'Unknown'),
                    "program": metadata.get('program', 'Unknown'),
                    "date": metadata.get('submission_date', 'Unknown').split('T')[0],
                    "status": metadata.get('status', 'Unknown'),
                    "student_id": metadata.get('student_id', 'Unknown'),
                    "document_id": results['ids'][i]
                })
        
        return applications
    except Exception as e:
        print(f"Error getting applications: {str(e)}")
        return []


# Function to update application status
def update_application_status(document_id, new_status):
    """Update the status of an application."""
    try:
        # Ensure collection exists
        admissions_collection = get_collection("admissions")
        
        # Get the existing application
        result = admissions_collection.get(ids=[document_id])
        if result and result['documents'] and result['documents'][0]:
            app_data = json.loads(result['documents'][0])
            
            # Update the status
            app_data['status'] = new_status
            
            # Update metadata
            metadata = result['metadatas'][0] if result['metadatas'] and result['metadatas'][0] else {}
            metadata['status'] = new_status
            
            # Update the document in the collection
            admissions_collection.update(
                ids=[document_id],
                documents=[json.dumps(app_data)],
                metadatas=[metadata]
            )
            return True
        return False
    except Exception as e:
        st.error(f"Error updating application status: {str(e)}")
        return False

# New function to handle ShortlistingAgent evaluation
async def run_shortlisting_evaluation(document_id):
    """Run the ShortlistingAgent evaluation for an application."""
    try:
        # Initialize the ShortlistingAgent
        agent = ShortlistingAgent()
        
        # Evaluate the application
        result = await agent.evaluate_application(document_id)
        
        return result
    except Exception as e:
        st.error(f"Error during shortlisting evaluation: {str(e)}")
        return None

# New function to batch process applications
async def run_batch_shortlisting(program=None):
    """Run batch evaluation for all applications ready for shortlisting."""
    try:
        # Initialize the ShortlistingAgent
        agent = ShortlistingAgent()
        
        # Run batch evaluation
        results = await agent.batch_evaluate(program)
        
        return results
    except Exception as e:
        st.error(f"Error during batch shortlisting: {str(e)}")
        return None

# New function to check program capacity
async def check_program_capacity(program):
    """Check the capacity for a specific program."""
    try:
        # Initialize the ShortlistingAgent
        agent = ShortlistingAgent()
        
        # Evaluate capacity
        result = await agent.evaluate_capacity(program)
        
        return result
    except Exception as e:
        st.error(f"Error checking program capacity: {str(e)}")
        return None

# Ensure ChromaDB is initialized
initialize_chroma_db()
# Render sidebar for navigation
render_sidebar()

# Render header
render_header("Admission Application", "Begin your academic journey")

# Check if user is logged in and their role
user_role = st.session_state.get("user_role")

if user_role == "student":
    # Student view - Application form or status
    student_id = st.session_state.get("student_id")
    
    if not student_id:
        st.warning("Please log in to access the application form")
        st.stop()
    
    # Check if student has an existing application
    application_data = get_student_application(student_id)
    
    if application_data:
        # Display application status
        st.success("Your application has been submitted successfully!")
        
        st.subheader("Application Details")
        st.markdown(f"**Application ID:** {application_data['id']}")
        st.markdown(f"**Date Submitted:** {application_data.get('submission_date', 'Unknown').split('T')[0]}")
        st.markdown(f"**Program Applied:** {application_data['program_applying_for']}")
        
        # Status tracker
        st.subheader("Application Status")
        status_options = ["Submitted", "Documents Verified", "Under Review", "Interview", "Decision"]
        current_status = application_data.get('status', 'Submitted')
        
        # Find status index (default to Submitted if not found)
        try:
            current_status_index = status_options.index(current_status)
        except ValueError:
            current_status_index = 0
        
        # Create status progress bar
        status_progress = st.progress(0)
        status_progress.progress((current_status_index + 1) / len(status_options))
        
        # Display current status
        st.info(f"**Current Status:** {current_status}")
        
        # Check documents status
        documents_collection = get_collection("documents")
        documents_results = documents_collection.get(
            where={"student_id": student_id}
        )
        
        pending_documents = []
        if documents_results and documents_results['documents']:
            for i, doc in enumerate(documents_results['documents']):
                if doc:
                    doc_data = json.loads(doc)
                    if doc_data.get('status') != "Verified":
                        pending_documents.append(doc_data.get('document_name', 'Unknown Document'))
        else:
            pending_documents = ["Official Transcripts", "ID/Passport", "Proof of Residence", "Recommendation Letter"]
            
        # Display next steps
        st.subheader("Next Steps")
        if pending_documents:
            for doc in pending_documents:
                st.warning(f"• Upload required document: {doc}")
            
            st.markdown("Please complete document submission to proceed with your application")
        else:
            st.success("All required documents submitted! Your application is under review.")
        
        # Display shortlisting results if available
        if 'shortlisting_results' in application_data:
            st.subheader("Evaluation Results")
            
            results = application_data['shortlisting_results']
            
            # Display overall score with color based on recommendation
            overall_score = results.get('overall_score', 0)
            recommendation = results.get('recommendation', '')
            
            # Create a color-coded score display
            score_color = "green" if overall_score >= 7.0 else "orange" if overall_score >= 5.0 else "red"
            st.markdown(f"<h3 style='color: {score_color}'>Score: {overall_score:.1f}/10</h3>", unsafe_allow_html=True)
            
            # Show detailed scores
            st.subheader("Evaluation Details")
            
            scores = results.get('scores', {})
            for key, value in scores.items():
                if isinstance(value, (int, float)):
                    st.markdown(f"**{key}:** {value:.1f}")
                else:
                    st.markdown(f"**{key}:** {value}")
            
            # Show the recommendation
            st.subheader("Recommendation")
            st.markdown(recommendation)
    
    else:
        # New application form
        st.subheader("Personal Information")
        
        col1, col2 = st.columns(2)
        with col1:
            first_name = st.text_input("First Name")
            date_of_birth = st.date_input("Date of Birth", min_value=datetime(1950, 1, 1))
            gender = st.selectbox("Gender", ["Select", "Male", "Female", "Non-binary", "Prefer not to say"])
            phone = st.text_input("Phone Number")
            
        with col2:
            last_name = st.text_input("Last Name")
            email = st.text_input("Email Address")
            nationality = st.text_input("Nationality")
            address = st.text_area("Address", height=100)
        
        st.subheader("Academic Information")
        
        col1, col2 = st.columns(2)
        with col1:
            education_level = st.selectbox("Highest Education Level", 
                                          ["Select", "High School", "Associate's Degree", "Bachelor's Degree",
                                           "Master's Degree", "Doctorate"])
            institution = st.text_input("Institution Name")
            graduation_year = st.number_input("Year of Graduation", min_value=1980, max_value=2025)
            
        with col2:
            program_applying_for = st.selectbox("Program Applying For", 
                                           ["Select", "Computer Science, B.Sc.",
                                            "Business Administration, B.B.A.",
                                            "Mechanical Engineering, B.Eng.",
                                            "Psychology, B.A.",
                                            "Data Science, M.Sc.",
                                            "MBA"])
            gpa = st.number_input("GPA", min_value=0.0, max_value=10.0, step=0.1)
            semester = st.selectbox("Starting Semester", ["Fall 2025", "Spring 2026", "Fall 2026"])
        
        st.subheader("Additional Information")
        
        extracurricular = st.text_area("Extracurricular Activities", 
                                       placeholder="Please list relevant extracurricular activities, awards, or achievements")
        
        statement = st.text_area("Personal Statement", 
                                placeholder="Why do you want to join this program? What are your career goals?", 
                                height=200)
        
        funding = st.selectbox("How do you plan to fund your education?", 
                              ["Select", "Self-funded", "Scholarship", "Student Loan", "Family Support", "Employer Sponsored"])
        
        # File upload placeholders - actual upload would be in document_upload.py
        st.subheader("Required Documents")
        st.info("You will be able to upload these documents after submitting your application form")
        st.markdown("""
        - Official Transcripts
        - ID or Passport Copy
        - Resume/CV
        - Recommendation Letters
        """)
        
        # Terms and conditions
        agree = st.checkbox("I certify that all information provided is true and complete to the best of my knowledge")
        
        if st.button("Submit Application", disabled=not agree):
            if not first_name or not last_name or not email or gender == "Select" or program_applying_for == "Select":
                st.error("Please fill out all required fields")
            else:
                # Create application data
                application_data = {
                    "student_id": student_id,
                    "first_name": first_name,
                    "last_name": last_name,
                    "date_of_birth": date_of_birth.isoformat(),
                    "gender": gender,
                    "phone": phone,
                    "email": email,
                    "nationality": nationality,
                    "address": address,
                    "education_level": education_level,
                    "institution": institution,
                    "graduation_year": graduation_year,
                    "program_applying_for": program_applying_for,
                    "gpa": gpa,
                    "semester": semester,
                    "extracurricular": extracurricular,
                    "statement": statement,
                    "funding": funding,
                    "status": "Under Review",
                    "submission_date": datetime.now().isoformat()
                }
                
                # Save application to ChromaDB
                document_id = save_application(application_data)
                
                st.success(f"Application submitted successfully! Your application ID is {document_id}")
                st.info("Please proceed to document upload section to complete your application")
                
                # Rerun to show status page
                st.rerun()

elif user_role == "admin":
    # Admin view - Applications dashboard
    st.subheader("Applications Dashboard")
    
    # Add tabs for different admin functions
    admin_tabs = st.tabs(["Applications List", "Shortlisting Management", "Program Capacity"])
    
    with admin_tabs[0]:  # Applications List tab
        # Filter options
        col1, col2, col3 = st.columns(3)
        with col1:
            status_filter = st.selectbox("Filter by Status", ["All", "Under Review", "Documents Verified", "Interview", "Accepted", "Rejected", "shortlisted"])
        with col2:
            program_filter = st.selectbox("Filter by Program", ["All", "Computer Science, B.Sc.", "Business Administration, B.B.A.", "Mechanical Engineering, B.Eng.", "Psychology, B.A.", "Data Science, M.Sc.", "MBA"])
        with col3:
            date_filter = st.date_input("Applications Since", datetime(2025, 1, 1))
        
        # Search box
        search = st.text_input("Search by Name or ID")
        
        # Get applications data from ChromaDB
        applications_data = get_all_applications(
            status_filter=status_filter, 
            program_filter=program_filter, 
            date_filter=date_filter.isoformat() if date_filter else None,
            search_term=search
        )
        
        if applications_data:
            # Convert to DataFrame for display
            df = pd.DataFrame(applications_data)
            # Keep only display columns
            display_df = df[["id", "name", "program", "date", "status"]]
            
            # Display applications table
            st.dataframe(display_df, use_container_width=True)
            
            # Application detail section
            st.subheader("Application Details")
            
            selected_app = st.selectbox(
                "Select Application to Review", 
                [f"{app['id']} - {app['name']}" for app in applications_data],
                index=0
            )
            
            if selected_app:
                app_id = selected_app.split(" - ")[0]
                # Find the selected application in our data
                selected_app_data = next((app for app in applications_data if app['id'] == app_id), None)
                
                if selected_app_data:
                    # Get full application data
                    full_app_data = get_document("admissions", selected_app_data['document_id'])
                    
                    if full_app_data:
                        # Display application details in an organized way
                        tabs = st.tabs(["Personal Info", "Academic Info", "Additional Info", "Documents", "Shortlisting", "Actions"])
                        
                        with tabs[0]:
                            st.markdown("### Personal Information")
                            st.markdown(f"**Name:** {full_app_data.get('first_name', '')} {full_app_data.get('last_name', '')}")
                            st.markdown(f"**Email:** {full_app_data.get('email', '')}")
                            st.markdown(f"**Phone:** {full_app_data.get('phone', '')}")
                            st.markdown(f"**Gender:** {full_app_data.get('gender', '')}")
                            st.markdown(f"**Date of Birth:** {full_app_data.get('date_of_birth', '').split('T')[0]}")
                            st.markdown(f"**Nationality:** {full_app_data.get('nationality', '')}")
                            st.markdown(f"**Address:** {full_app_data.get('address', '')}")
                        
                        with tabs[1]:
                            st.markdown("### Academic Information")
                            st.markdown(f"**Education Level:** {full_app_data.get('education_level', '')}")
                            st.markdown(f"**Institution:** {full_app_data.get('institution', '')}")
                            st.markdown(f"**Graduation Year:** {full_app_data.get('graduation_year', '')}")
                            st.markdown(f"**Program Applied For:** {full_app_data.get('program_applying_for', '')}")
                            st.markdown(f"**GPA:** {full_app_data.get('gpa', '')}")
                            st.markdown(f"**Starting Semester:** {full_app_data.get('semester', '')}")
                        
                        with tabs[2]:
                            st.markdown("### Additional Information")
                            st.markdown("#### Extracurricular Activities")
                            st.markdown(full_app_data.get('extracurricular', 'None provided'))
                            
                            st.markdown("#### Personal Statement")
                            st.markdown(full_app_data.get('statement', 'None provided'))
                            
                            st.markdown(f"**Funding Plan:** {full_app_data.get('funding', 'Not specified')}")
                        
                        with tabs[3]:
                            st.markdown("### Document Status")
                            
                            # Get documents for this student
                            documents_collection = get_collection("documents")
                            documents_results = documents_collection.get(
                                where={"student_id": full_app_data.get('student_id')}
                            )
                            
                            if documents_results and documents_results['documents']:
                                # Create document status table
                                doc_data = []
                                for i, doc in enumerate(documents_results['documents']):
                                    if doc:
                                        doc_info = json.loads(doc)
                                        doc_data.append({
                                            "Document": doc_info.get('document_name', 'Unknown'),
                                            "Status": doc_info.get('status', 'Unknown'),
                                            "Uploaded": doc_info.get('upload_date', 'Unknown').split('T')[0]
                                        })
                                
                                if doc_data:
                                    st.table(pd.DataFrame(doc_data))
                                else:
                                    st.info("No documents uploaded yet")
                            else:
                                st.info("No documents uploaded yet")
                        
                        with tabs[4]:
                            st.markdown("### Shortlisting Evaluation")
                            
                            # Check if shortlisting has already been done
                            shortlisting_results = full_app_data.get('shortlisting_results', None)
                            
                            if shortlisting_results:
                                # Display existing shortlisting results
                                st.success("This application has been evaluated")
                                
                                # Overall score with color indicator
                                overall_score = shortlisting_results.get('overall_score', 0)
                                recommendation = shortlisting_results.get('recommendation', '')
                                
                                score_color = "green" if overall_score >= 7.0 else "orange" if overall_score >= 5.0 else "red"
                                st.markdown(f"<h3 style='color: {score_color}'>Overall Score: {overall_score:.1f}/10</h3>", unsafe_allow_html=True)
                                
                                # Detailed scores
                                st.subheader("Evaluation Criteria")
                                scores = shortlisting_results.get('scores', {})
                                
                                # Convert scores to DataFrame for better display
                                score_data = []
                                for key, value in scores.items():
                                    if isinstance(value, (int, float)):
                                        score_data.append({"Criterion": key, "Score": f"{value:.1f}"})
                                    else:
                                        score_data.append({"Criterion": key, "Score": value})
                                
                                if score_data:
                                    st.table(pd.DataFrame(score_data))
                                
                                # Recommendation
                                st.subheader("Recommendation")
                                st.markdown(recommendation)
                                
                                # Full evaluation
                                with st.expander("View Full Evaluation"):
                                    st.markdown(shortlisting_results.get('evaluation', 'No detailed evaluation available'))
                                
                                # Re-evaluate button
                                if st.button("Re-evaluate Application"):
                                    # First update status to shortlisted
                                    update_application_status(selected_app_data['document_id'], "shortlisted")
                                    
                                    # Show evaluation in progress
                                    with st.spinner("Evaluating application..."):
                                        # Run the shortlisting evaluation
                                        result = asyncio.run(run_shortlisting_evaluation(app_id))
                                        
                                        if result:
                                            st.success("Application re-evaluated successfully!")
                                            st.rerun()
                            else:
                                # No existing evaluation, offer to run one
                                st.info("This application has not been evaluated yet")
                                
                                # Check if application is ready for shortlisting
                                if selected_app_data['status'] == "document_verification" or selected_app_data['status'] == "Under Review":
                                    # First update status to shortlisted
                                    if st.button("Mark for Shortlisting"):
                                        update_application_status(selected_app_data['document_id'], "shortlisted")
                                        st.success("Application marked for shortlisting")
                                        st.rerun()
                                
                                if selected_app_data['status'] == "shortlisted":
                                    if st.button("Run Shortlisting Evaluation"):
                                        # Show evaluation in progress
                                        with st.spinner("Evaluating application..."):
                                            # Run the shortlisting evaluation
                                            result = asyncio.run(run_shortlisting_evaluation(app_id))
                                            
                                            if result:
                                                st.success("Application evaluated successfully!")
                                                st.rerun()
                        
                        with tabs[5]:
                            st.markdown("### Application Actions")
                            
                            # Current status
                            st.info(f"Current Status: {selected_app_data['status']}")
                            
                            # Action buttons
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                if st.button("Accept Application"):
                                    if update_application_status(selected_app_data['document_id'], "Accepted"):
                                        st.success(f"Application {app_id} has been accepted")
                                        st.rerun()
                            with col2:
                                if st.button("Schedule Interview"):
                                    if update_application_status(selected_app_data['document_id'], "Interview"):
                                        st.success(f"Application {app_id} moved to Interview stage")
                                        st.rerun()
                            with col3:
                                if st.button("Reject Application"):
                                    reason = st.text_input("Rejection reason:")
                                    if reason and st.button("Confirm Rejection"):
                                        if update_application_status(selected_app_data['document_id'], "Rejected"):
                                            # In a real system, you'd store the reason too
                                            st.error(f"Application {app_id} has been rejected")
                                            st.rerun()
                    else:
                        st.error("Could not retrieve application details")
        else:
            st.info("No applications found matching your criteria")
    
    with admin_tabs[1]:  # Shortlisting Management tab
        st.subheader("Batch Shortlisting")
        
        # Program selection for batch shortlisting
        batch_program = st.selectbox(
            "Select Program for Batch Shortlisting",
            ["All Programs", "Computer Science, B.Sc.", "Business Administration, B.B.A.", "Mechanical Engineering, B.Eng.", 
             "Psychology, B.A.", "Data Science, M.Sc.", "MBA"]
        )
        
        # Run batch shortlisting
        if st.button("Run Batch Shortlisting"):
            with st.spinner("Processing applications..."):
                program = None if batch_program == "All Programs" else batch_program
                results = asyncio.run(run_batch_shortlisting(program))
                
                if results:
                    st.success(f"Successfully evaluated {results.get('evaluated_count', 0)} applications")
                    
                    # Display results summary
                    result_data = []
                    for app_id, result in results.get('results', {}).items():
                        result_data.append({
                            "Application ID": app_id,
                            "Status": result.get('status', 'Unknown'),
                            "Score": result.get('overall_score', 'N/A'),
                            "Recommendation": result.get('recommendation', 'N/A')[:50] + '...' if result.get('recommendation') and len(result.get('recommendation')) > 50 else result.get('recommendation', 'N/A')
                        })
                    
                    if result_data:
                        st.dataframe(pd.DataFrame(result_data))
                    else:
                        st.info("No applications were processed")
        
        # Applications awaiting shortlisting
        st.subheader("Applications Ready for Shortlisting")
        
        # Get applications marked for shortlisting but not yet evaluated
        shortlisting_apps = get_all_applications(status_filter="shortlisted")
        
        if shortlisting_apps:
            # Show in a concise format
            shortlist_data = [{
                "ID": app['id'],
                "Name": app['name'],
                "Program": app['program'],
                "Date": app['date']
            } for app in shortlisting_apps]
            
            st.dataframe(pd.DataFrame(shortlist_data))
            
            # Bulk action buttons
            if st.button("Mark All as Shortlisted"):
                # Get applications ready for shortlisting
                ready_apps = get_all_applications(status_filter="document_verification")
                
                count = 0
                for app in ready_apps:
                    if update_application_status(app['document_id'], "shortlisted"):
                        count += 1
                
                if count > 0:
                    st.success(f"Marked {count} applications for shortlisting")
                    st.rerun()
                else:
                    st.info("No applications to mark for shortlisting")
        else:
            st.info("No applications are currently marked for shortlisting")
    
    with admin_tabs[2]:  # Program Capacity tab
        st.subheader("Program Capacity Management")
        
        # Program selection for capacity check
        capacity_program = st.selectbox(
            "Select Program to Check Capacity",
            ["Computer Science, B.Sc.", "Business Administration, B.B.A.", "Mechanical Engineering, B.Eng.", 
             "Psychology, B.A.", "Data Science, M.Sc.", "MBA"]
        )
        
        # Run capacity check
        if st.button("Check Program Capacity"):
            with st.spinner("Analyzing program capacity..."):
                result = asyncio.run(check_program_capacity(capacity_program))
                
                if result:
                    # Display capacity information
                    st.success("Capacity analysis complete")
                    
                    # Create a visual representation of capacity
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric("Total Capacity", result.get('capacity', 'Unknown'))
                        st.metric("Accepted Applications", result.get('accepted_count', 0))
                        st.metric("Pending Applications", result.get('pending_count', 0))
                        st.metric("Available Slots", result.get('available_slots', 0))
                    
                    with col2:
                        # Create a simple pie chart using html/css
                        accepted = result.get('accepted_count', 0)
                        pending = result.get('pending_count', 0)
                        available = result.get('available_slots', 0)
                        total = accepted + pending + available
                        
                        if total > 0:
                            accepted_pct = int(accepted / total * 100)
                            pending_pct = int(pending / total * 100)
                            available_pct = 100 - accepted_pct - pending_pct
                            # Visual capacity display
                            st.markdown(f"""
                                <div style="width:100%; height:30px; border-radius:15px; overflow:hidden; display:flex">
                                    <div style="width:{accepted_pct}%; height:100%; background-color:#ff4b4b; text-align:center; color:white">
                                        {accepted_pct}%
                                    </div>
                                    <div style="width:{pending_pct}%; height:100%; background-color:#ffa64b; text-align:center; color:white">
                                        {pending_pct}%
                                    </div>
                                    <div style="width:{available_pct}%; height:100%; background-color:#4bff4b; text-align:center; color:white">
                                        {available_pct}%
                                    </div>
                                </div>
                                <div style="display:flex; justify-content:space-between; width:100%; margin-top:5px">
                                    <div>Accepted</div>
                                    <div>Pending</div>
                                    <div>Available</div>
                                </div>
                            """, unsafe_allow_html=True)
                    
                    # Display the analysis from the ShortlistingAgent
                    st.subheader("Capacity Analysis")
                    st.markdown(result.get('analysis', 'No analysis available'))
                    
                    # Add capacity management actions
                    st.subheader("Capacity Management Actions")
                    
                    if result.get('available_slots', 0) <= 0:
                        st.warning("This program has reached its capacity!")
                        
                        if st.button("Request Capacity Increase"):
                            st.success("Capacity increase request has been submitted to the administration")
                            # In a real system, this would trigger a notification or workflow
                    
                    # Display applications by priority
                    st.subheader("Shortlisted Applications by Priority")
                    
                    # Get applications shortlisted for this program
                    program_apps = get_all_applications(
                        status_filter="shortlisted", 
                        program_filter=capacity_program
                    )
                    
                    if program_apps:
                        # We'd need to get the shortlisting results for each application
                        priority_apps = []
                        for app in program_apps:
                            full_app = get_document("admissions", app['document_id'])
                            if full_app and 'shortlisting_results' in full_app:
                                priority_apps.append({
                                    "id": app['id'],
                                    "name": app['name'],
                                    "score": full_app['shortlisting_results'].get('overall_score', 0),
                                    "document_id": app['document_id']
                                })
                        
                        # Sort by score (highest first)
                        priority_apps.sort(key=lambda x: x['score'], reverse=True)
                        
                        # Display as a table
                        if priority_apps:
                            priority_df = pd.DataFrame(priority_apps)
                            st.dataframe(priority_df[["id", "name", "score"]])
                            
                            # Auto-accept top applications based on available slots
                            available_slots = result.get('available_slots', 0)
                            if available_slots > 0 and st.button(f"Auto-accept Top {min(available_slots, len(priority_apps))} Applications"):
                                accepted_count = 0
                                for i, app in enumerate(priority_apps):
                                    if i < available_slots:
                                        if update_application_status(app['document_id'], "Accepted"):
                                            accepted_count += 1
                                
                                if accepted_count > 0:
                                    st.success(f"Successfully accepted {accepted_count} top applications")
                                    st.rerun()
                        else:
                            st.info("No shortlisted applications with evaluation results")
                    else:
                        st.info("No shortlisted applications for this program")

else:
    # Not logged in view
    st.warning("Please log in to fill out an application or view your application status")
    
    st.info("For new students: Please register using the sidebar to start your application")

# Render footer
render_footer()