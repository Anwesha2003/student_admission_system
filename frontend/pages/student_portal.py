import streamlit as st
import pandas as pd
from datetime import datetime
import json
import uuid

from components.sidebar import render_sidebar
from components.header import render_header
from components.footer import render_footer
from backend.database.chroma_client import get_document, query_documents, get_collection, add_document, update_document, delete_document

render_sidebar()
render_header("Student Portal", "Track your application progress")

# At the beginning of your script
if 'application_status' not in st.session_state:
    st.session_state.application_status = "Not Started"
if 'documents_verified' not in st.session_state:
    st.session_state.documents_verified = "0/4"
if 'decision_estimate' not in st.session_state:
    st.session_state.decision_estimate = "N/A"

user_role = st.session_state.get("user_role")
student_id = st.session_state.get("student_id")

if user_role != "student":
    st.warning("You must be logged in as a student to access this portal")
    st.stop()

# Retrieve student data from ChromaDB
student_data = get_document("students", student_id)
if not student_data:
    # Create a new student record if it doesn't exist
    student_data = {
        "id": student_id,
        "name": f"Student {student_id}",
        "program": "Computer Science, B.Sc.",
        "application_date": datetime.now().strftime("%Y-%m-%d"),
        "application_status": "Under Review",
        "documents_verified": "2/4",
        "decision_estimate": "10 days"
    }
    add_document("students", student_data, student_id, {"id": student_id})

st.subheader(f"Welcome, {student_data.get('name', f'Student {student_id}')}")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Application Status", student_data.get("application_status", "Under Review"), 
              help="Current status of your application")

with col2:
    st.metric("Documents Verified", student_data.get("documents_verified", "2/4"), 
              delta="-2", help="Number of verified documents")

with col3:
    st.metric("Estimated Decision", student_data.get("decision_estimate", "10 days"), 
              delta="-2 days", help="Estimated time until final decision")

st.subheader("Application Overview")

tab1, tab2, tab3, tab4 = st.tabs(["Status Timeline", "Documents", "Messages", "Financial Aid"])

with tab1:
    st.markdown("### Your Application Timeline")
    
    # Query timeline events from ChromaDB
    timeline_events_query = query_documents(
        "admissions", 
        f"student:{student_id} timeline", 
        n_results=10, 
        metadata_filter={"student_id": student_id}
    )
    
    # Use query results if available, otherwise use sample data
    if timeline_events_query:
        timeline_events = timeline_events_query
    else:
        # Sample data that would be added to ChromaDB in a real application
        timeline_events = [
            {"date": "Mar 15, 2025", "event": "Application Submitted", "status": "Completed", "details": "Your application for Computer Science, B.Sc. has been received."},
            {"date": "Mar 16, 2025", "event": "Document Verification", "status": "In Progress", "details": "2 of 4 required documents have been verified."},
            {"date": "Pending", "event": "Application Review", "status": "Queued", "details": "Your application will be reviewed once all documents are verified."},
            {"date": "Pending", "event": "Interview", "status": "Not Started", "details": "You may be invited for an interview based on your application."},
            {"date": "Pending", "event": "Final Decision", "status": "Not Started", "details": "The admissions committee will make a final decision."}
        ]
        
        # Add these events to ChromaDB for future reference
        for idx, event in enumerate(timeline_events):
            event_id = f"{student_id}_timeline_{idx}"
            add_document(
                "admissions", 
                event, 
                event_id,
                {"student_id": student_id, "type": "timeline_event"}
            )
    
    for event in timeline_events:
        col1, col2, col3 = st.columns([1, 2, 4])
        
        with col1:
            st.write(event.get("date", "Pending"))
        
        with col2:
            status = event.get("status", "Not Started")
            if status == "Completed":
                st.success(event.get("event", ""))
            elif status == "In Progress":
                st.info(event.get("event", ""))
            elif status == "Queued":
                st.warning(event.get("event", ""))
            else:
                st.text(event.get("event", ""))
        
        with col3:
            st.write(event.get("details", ""))
    
    # Calculate progress based on completed events
    completed_events = sum(1 for event in timeline_events if event.get("status") == "Completed")
    progress_percentage = completed_events / len(timeline_events)
    
    st.progress(progress_percentage)
    st.caption(f"Application Progress: {int(progress_percentage * 100)}%")

with tab2:
    st.markdown("### Required Documents")
    
    # Query documents from ChromaDB
    required_docs_query = query_documents(
        "documents", 
        f"student:{student_id} required documents", 
        n_results=10, 
        metadata_filter={"student_id": student_id, "type": "required_document"}
    )
    
    # Use query results if available, otherwise use sample data
    if required_docs_query:
        documents = required_docs_query
    else:
        # Sample data that would be added to ChromaDB in a real application
        documents = [
            {"name": "Official Transcript", "status": "Verified", "submitted": "Mar 15, 2025", "verified": "Mar 16, 2025"},
            {"name": "ID/Passport Copy", "status": "Rejected", "submitted": "Mar 15, 2025", "notes": "Document unclear or incomplete. Please resubmit."},
            {"name": "Personal Statement", "status": "Verified", "submitted": "Mar 15, 2025", "verified": "Mar 16, 2025"},
            {"name": "Recommendation Letter", "status": "Not Submitted", "notes": "Required for application completion"}
        ]
        
        # Add these documents to ChromaDB for future reference
        for idx, doc in enumerate(documents):
            doc_id = f"{student_id}_document_{idx}"
            add_document(
                "documents", 
                doc,
                doc_id,
                {"student_id": student_id, "type": "required_document", "name": doc["name"]}
            )
    
    for idx, doc in enumerate(documents):
        expander_label = f"{doc.get('name', f'Document {idx}')} - {doc.get('status', 'Unknown')}"
        
        with st.expander(expander_label):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Status:** {doc.get('status', 'Unknown')}")
                st.write(f"**Submitted:** {doc.get('submitted', 'Not yet')}")
                
                doc_status = doc.get('status', '')
                
                if doc_status == 'Verified':
                    st.write(f"**Verified On:** {doc.get('verified', 'Unknown')}")
                elif doc_status == 'Rejected':
                    st.error(f"**Reason:** {doc.get('notes', 'No reason provided')}")
                    uploaded_file = st.file_uploader(f"Upload new {doc.get('name', 'document')}", key=f"reupload_{idx}")
                    if uploaded_file:
                        if st.button(f"Submit {doc.get('name', 'document')}", key=f"submit_rejected_{idx}"):
                            # Update document status in ChromaDB
                            doc_id = f"{student_id}_document_{idx}"
                            doc_updated = doc.copy()
                            doc_updated["status"] = "Pending"
                            doc_updated["submitted"] = datetime.now().strftime("%Y-%m-%d")
                            update_document(
                                "documents", 
                                doc_id, 
                                doc_updated,
                                {"student_id": student_id, "type": "required_document", "name": doc["name"]}
                            )
                            st.success(f"New {doc.get('name', 'document')} submitted successfully")
                            st.rerun()
                elif doc_status == 'Not Submitted':
                    st.warning(f"**Note:** {doc.get('notes', 'Required document')}")
                    uploaded_file = st.file_uploader(f"Upload {doc.get('name', 'document')}", key=f"upload_{idx}")
                    if uploaded_file:
                        if st.button(f"Submit {doc.get('name', 'document')}", key=f"submit_new_{idx}"):
                            # Update document status in ChromaDB
                            doc_id = f"{student_id}_document_{idx}"
                            doc_updated = doc.copy()
                            doc_updated["status"] = "Pending"
                            doc_updated["submitted"] = datetime.now().strftime("%Y-%m-%d")
                            update_document(
                                "documents", 
                                doc_id, 
                                doc_updated,
                                {"student_id": student_id, "type": "required_document", "name": doc["name"]}
                            )
                            st.success(f"{doc.get('name', 'document')} submitted successfully")
                            st.rerun()
            
            with col2:
                if doc.get('status') == 'Verified':
                    st.success("This document has been verified successfully.")
                elif doc.get('status') == 'Rejected':
                    st.error("This document was rejected. Please upload a new version.")
                elif doc.get('status') == 'Not Submitted':
                    st.warning("This document needs to be submitted.")
                elif doc.get('status') == 'Pending':
                    st.info("This document is being reviewed.")

with tab3:
    st.markdown("### Messages & Notifications")
    
    # Query messages from ChromaDB
    messages_query = query_documents(
        "documents", 
        f"student:{student_id} messages", 
        n_results=10, 
        metadata_filter={"student_id": student_id, "type": "message"}
    )
    
    # Use query results if available, otherwise use sample data
    if messages_query:
        messages = messages_query
    else:
        # Sample data that would be added to ChromaDB in a real application
        messages = [
            {"date": "Mar 16, 2025", "sender": "Document Verification Team", "subject": "ID Document Rejected", "read": True, "content": "Dear Applicant,\n\nWe regret to inform you that your ID document has been rejected due to poor image quality. Please upload a clear, high-resolution scan or photo of your government-issued ID.\n\nBest regards,\nDocument Verification Team"},
            {"date": "Mar 15, 2025", "sender": "Admissions Office", "subject": "Application Received", "read": True, "content": "Dear Applicant,\n\nWe are pleased to confirm that we have received your application for admission to the Computer Science, B.Sc. program. Our team will review your application once all required documents have been verified.\n\nBest regards,\nAdmissions Office"},
            {"date": "Mar 15, 2025", "sender": "System", "subject": "Welcome to the University Admissions Portal", "read": True, "content": "Welcome to the University Admissions Portal! We're excited to have you here. Please complete all required steps to finalize your application."}
        ]
        
        # Add these messages to ChromaDB for future reference
        for idx, msg in enumerate(messages):
            msg_id = f"{student_id}_message_{idx}"
            add_document(
                "documents", 
                msg,
                msg_id,
                {"student_id": student_id, "type": "message", "sender": msg["sender"]}
            )
    
    for idx, msg in enumerate(messages):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if not msg.get("read", True):
                st.markdown(f"**{msg.get('subject', 'No subject')}** - {msg.get('sender', 'Unknown')}")
            else:
                st.write(f"{msg.get('subject', 'No subject')} - {msg.get('sender', 'Unknown')}")
        
        with col2:
            st.write(msg.get("date", "Unknown date"))
        
        view_key = f"view_{idx}"
        if st.button("View", key=view_key):
            msg_content = msg.get("content", "No content available")
            st.info(msg_content)
            
            # Mark as read in ChromaDB if not already read
            if not msg.get("read", True):
                msg_id = f"{student_id}_message_{idx}"
                msg_updated = msg.copy()
                msg_updated["read"] = True
                update_document(
                    "documents", 
                    msg_id, 
                    msg_updated,
                    {"student_id": student_id, "type": "message", "sender": msg["sender"]}
                )
    
    message_text = st.text_area("Send a message to the admissions team", height=100)
    
    if st.button("Send Message"):
        if message_text:
            # Add new message to ChromaDB
            new_msg = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "sender": f"Student {student_id}",
                "subject": "Message from Student",
                "read": False,
                "content": message_text,
                "to": "Admissions Office"
            }
            
            msg_id = f"{student_id}_message_outgoing_{uuid.uuid4()}"
            add_document(
                "documents", 
                new_msg,
                msg_id,
                {"student_id": student_id, "type": "message", "sender": f"Student {student_id}"}
            )
            
            st.success("Message sent successfully")
            st.rerun()
        else:
            st.error("Please enter a message before sending")

with tab4:
    st.markdown("### Financial Aid & Loans")
    
    # Query financial data from ChromaDB
    financial_data_query = query_documents(
        "loans", 
        f"student:{student_id} financial aid", 
        n_results=5, 
        metadata_filter={"student_id": student_id, "type": "loan_application"}
    )
    
    # Check if there's existing loan application data
    has_loan_application = len(financial_data_query) > 0
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Estimated Costs")
        
        # Query fee structure from ChromaDB
        fee_structure = query_documents("fee_structure", "Computer Science bachelor", n_results=1)
        
        if fee_structure:
            costs_data = fee_structure[0].get("costs", {})
        else:
            # Default costs
            costs_data = {
                'Tuition': '$25,000',
                'Housing': '$12,000',
                'Books': '$1,500',
                'Other Fees': '$2,500',
                'Total': '$41,000'
            }
        
        costs = pd.DataFrame({
            'Expense': list(costs_data.keys()),
            'Amount': list(costs_data.values())
        })
        
        st.table(costs)
        
        st.markdown("#### Financial Aid Status")
        
        if has_loan_application:
            loan_data = financial_data_query[0]
            loan_status = loan_data.get("status", "Processing")
            
            if loan_status == "Approved":
                st.success(f"Your loan application has been approved for {loan_data.get('amount_approved', 'Unknown amount')}")
            elif loan_status == "Pending":
                st.info("Your loan application is being processed")
            elif loan_status == "Denied":
                st.error(f"Your loan application was denied. Reason: {loan_data.get('denial_reason', 'No reason provided')}")
                
                if st.button("Submit New Application"):
                    st.switch_page("pages/loan_application.py")
            else:
                st.warning(f"Status: {loan_status}")
        else:
            st.info("You have not applied for financial aid yet.")
            
            if st.button("Apply for Financial Aid"):
                st.switch_page("pages/loan_application.py")
    
    with col2:
        st.markdown("#### Scholarships You May Qualify For")
        
        # Query scholarships from ChromaDB
        scholarships_query = query_documents(
            "eligibility_criteria", 
            "scholarships", 
            n_results=5
        )
        
        if scholarships_query:
            scholarships = scholarships_query
        else:
            # Sample data
            scholarships = [
                {"name": "Academic Excellence Scholarship", "amount": "Up to $10,000", "deadline": "Apr 15, 2025", "requirements": "GPA of 3.5 or higher\nStrong academic record\nEssay submission"},
                {"name": "STEM Leaders Award", "amount": "Up to $5,000", "deadline": "Apr 30, 2025", "requirements": "STEM major\nDemonstrated leadership\nTwo recommendation letters"},
                {"name": "Diversity in Computing Grant", "amount": "Up to $7,500", "deadline": "May 15, 2025", "requirements": "Computer science major\nDemonstrated commitment to diversity\nPersonal statement"}
            ]
            
            # Add scholarships to ChromaDB
            for idx, scholarship in enumerate(scholarships):
                scholarship_id = f"scholarship_{idx}"
                add_document(
                    "eligibility_criteria", 
                    scholarship,
                    scholarship_id,
                    {"type": "scholarship"}
                )
        
        for idx, scholarship in enumerate(scholarships):
            with st.expander(f"{scholarship.get('name', f'Scholarship {idx}')} - {scholarship.get('amount', 'Unknown amount')}"):
                st.write(f"**Amount:** {scholarship.get('amount', 'Unknown')}")
                st.write(f"**Application Deadline:** {scholarship.get('deadline', 'Unknown')}")
                
                if "requirements" in scholarship:
                    st.write(f"**Requirements:**\n{scholarship['requirements']}")
                
                apply_key = f"apply_scholarship_{idx}"
                if st.button("Apply", key=apply_key):
                    # Record application in ChromaDB
                    application = {
                        "student_id": student_id,
                        "scholarship_name": scholarship.get('name', f'Scholarship {idx}'),
                        "application_date": datetime.now().strftime("%Y-%m-%d"),
                        "status": "Submitted"
                    }
                    
                    document_id = f"{student_id}_scholarship_{uuid.uuid4()}"
                    add_document(
                        "eligibility_criteria", 
                        application,
                        document_id,
                        {"student_id": student_id, "type": "scholarship_application"}
                    )
                    
                    st.success("Scholarship application initiated")
                    st.rerun()

st.subheader("AI Assistant")

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = [
        {"role": "assistant", "content": "Hello! I'm your AI admission assistant. How can I help you with your application today?"}
    ]

for message in st.session_state.chat_messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

user_input = st.chat_input("Ask a question about your application...")

if user_input:
    # Add user message to chat history
    st.session_state.chat_messages.append({"role": "user", "content": user_input})
    
    with st.chat_message("user"):
        st.write(user_input)
    
    # Store the chat message in ChromaDB
    chat_message = {
        "student_id": student_id,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "content": user_input,
        "role": "user"
    }
    
    chat_id = f"{student_id}_chat_{uuid.uuid4()}"
    add_document(
        "documents", 
        chat_message,
        chat_id,
        {"student_id": student_id, "type": "chat_message"}
    )
    
    # Query relevant information from ChromaDB based on user query
    relevant_info = query_documents(
        "university_policies", 
        user_input, 
        n_results=2
    )
    
    # Generate AI response based on user query and relevant info
    if "recommendation letter" in user_input.lower() or "document" in user_input.lower():
        ai_response = "Thank you for your question. Based on your current application status, I recommend prioritizing the upload of your missing recommendation letter. This will help expedite your application review process. Would you like me to provide information about the recommendation letter requirements?"
    elif "financial aid" in user_input.lower() or "scholarship" in user_input.lower() or "loan" in user_input.lower():
        ai_response = "For financial aid, you can apply through the Financial Aid tab. Based on your profile, you may qualify for several scholarships, particularly the Academic Excellence Scholarship if your GPA is 3.5 or higher. Would you like specific information about loan options?"
    elif "timeline" in user_input.lower() or "decision" in user_input.lower() or "when" in user_input.lower():
        ai_response = "Once all your documents are verified, your application will move to the review stage. The admissions committee typically makes decisions within 2-3 weeks after all required materials are received. Currently, we estimate you'll receive a decision in approximately 10 days."
    elif len(relevant_info) > 0:
        # Use information from ChromaDB if available
        ai_response = f"Based on our university policies, I can tell you that: {relevant_info[0].get('content', 'Please check with the admissions office for more details.')}"
    else:
        ai_response = "Thank you for your question. I'd be happy to help with your application process. Please let me know if you have specific questions about your documents, timeline, financial aid options, or any other aspect of the admissions process."
    
    # Add AI response to chat history
    with st.chat_message("assistant"):
        st.write(ai_response)
    
    st.session_state.chat_messages.append({"role": "assistant", "content": ai_response})
    
    # Store the AI response in ChromaDB
    ai_chat_message = {
        "student_id": student_id,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "content": ai_response,
        "role": "assistant"
    }
    
    ai_chat_id = f"{student_id}_chat_{uuid.uuid4()}"
    add_document(
        "documents", 
        ai_chat_message,
        ai_chat_id,
        {"student_id": student_id, "type": "chat_message"}
    )

render_footer()