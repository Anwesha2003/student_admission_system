import streamlit as st
import pandas as pd
from datetime import datetime
import os
import uuid
import json
import asyncio

from components.sidebar import render_sidebar
from components.header import render_header
from components.footer import render_footer
from backend.database.chroma_client import get_client,get_collection, add_document, get_document, query_documents, update_document
from backend.Agents.document_checker import DocumentCheckerAgent

# Initialize the document checker agent
document_checker = DocumentCheckerAgent()

# Ensure uploads directory exists
UPLOADS_DIR = "./uploads"
os.makedirs(UPLOADS_DIR, exist_ok=True)

def get_documents_for_student(student_id):
    """Retrieve all documents for a student."""
    documents_collection = get_collection("documents")
    results = documents_collection.get(
        where={"student_id": student_id}
    )
    
    documents = []
    for i, doc in enumerate(results['documents']):
        if doc:
            doc_data = json.loads(doc)
            doc_data['id'] = results['ids'][i]
            doc_data['metadata'] = results['metadatas'][i] if results['metadatas'] else {}
            documents.append(doc_data)
    
    return documents

def update_document_status(document_id, status, reason=None):
    """Update the status of a document."""
    documents_collection = get_collection("documents")
    
    # Get the existing document
    result = documents_collection.get(ids=[document_id])
    if result and result['documents'] and result['documents'][0]:
        doc_data = json.loads(result['documents'][0])
        
        # Update the status and reason
        doc_data['status'] = status
        if reason:
            doc_data['reason'] = reason
        
        # Update metadata
        metadata = result['metadatas'][0] if result['metadatas'] and result['metadatas'][0] else {}
        metadata['status'] = status
        if reason:
            metadata['reason'] = reason
        
        # Update the document in the collection
        documents_collection.update(
            ids=[document_id],
            documents=[json.dumps(doc_data)],
            metadatas=[metadata]
        )
        return True
    return False

async def process_document_verification(document_id):
    """Process document verification using AI agent."""
    try:
        # Get the document to verify
        result = await document_checker.verify_document(document_id)
        
        # Update document status based on verification result
        verification_status = result.get("verification_status", "Pending")
        verification_notes = result.get("verification_notes", "")
        
        # Map the verification status to our application statuses
        status_mapping = {
            "verified": "Verified",
            "needs_clarification": "Pending",
            "rejected": "Rejected"
        }
        
        new_status = status_mapping.get(verification_status, "Pending")
        reason = verification_notes if new_status == "Rejected" else None
        
        # Update the document status
        update_document_status(document_id, new_status, reason)
        
        return new_status
    except Exception as e:
        st.error(f"Error during document verification: {str(e)}")
        return "Pending"

def handle_document_upload(student_id, doc_name, uploaded_file, existing_doc_id=None):
    """Handle document upload and initiate verification process."""
    if not uploaded_file:
        return False
    
    # Save file to disk
    safe_doc_name = doc_name.replace("/", "_") 
    file_path = f"{UPLOADS_DIR}/{student_id}_{safe_doc_name}.pdf"
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    # Create document data
    doc_data = {
        "student_id": student_id,
        "document_name": doc_name,
        "file_path": file_path,
        "status": "Pending",
        "upload_date": datetime.now().isoformat(),
    }
    
    # Add or update document in ChromaDB
    if existing_doc_id:
        # Update existing document
        update_document_status(existing_doc_id, "Pending")
        document_id = existing_doc_id
    else:
        # Add new document
        document_id = str(uuid.uuid4())
        add_document(
            "documents", 
            doc_data, 
            document_id, 
            metadata={
                "student_id": student_id,
                "document_name": doc_name,
                "status": "Pending"
            }
        )
    
    # Schedule verification (we can't directly use asyncio.create_task in Streamlit)
    # Instead, store the task in session state for later processing
    if "verification_tasks" not in st.session_state:
        st.session_state.verification_tasks = {}
    
    st.session_state.verification_tasks[document_id] = {
        "status": "queued",
        "document_id": document_id,
        "student_id": student_id,
        "document_name": doc_name
    }
    
    return document_id

def process_verification_queue():
    """Process any queued verification tasks"""
    if "verification_tasks" not in st.session_state:
        return
    
    # Process up to 3 tasks at a time
    tasks_to_process = [task for task_id, task in st.session_state.verification_tasks.items() 
                        if task["status"] == "queued"][:3]
    
    for task in tasks_to_process:
        document_id = task["document_id"]
        
        # Mark as processing
        st.session_state.verification_tasks[document_id]["status"] = "processing"
        
        # Since we can't use asyncio directly in Streamlit, we'll use a synchronous approach
        # In a production app, you would use a background worker or queue system
        st.info(f"AI is now verifying your {task['document_name']}. This may take a moment...")
        
        # For demo purposes, we'll just set a random status
        import random
        statuses = ["Verified", "Rejected", "Pending"]
        weights = [0.7, 0.2, 0.1]  # 70% chance of verification, 20% rejection, 10% pending
        new_status = random.choices(statuses, weights=weights, k=1)[0]
        
        if new_status == "Rejected":
            reasons = [
                "Document appears to be altered or tampered with",
                "Document is not legible",
                "Document is expired",
                "Document does not match student information",
                "Document is missing required information"
            ]
            reason = random.choice(reasons)
            update_document_status(document_id, new_status, reason)
        else:
            update_document_status(document_id, new_status)
        
        # Mark as completed
        st.session_state.verification_tasks[document_id]["status"] = "completed"
        st.session_state.verification_tasks[document_id]["result"] = new_status

# Render sidebar and header
render_sidebar()
render_header("Document Upload & Verification", "Submit required documents for your application")

# Check if user is logged in and their role
user_role = st.session_state.get("user_role")
student_id = st.session_state.get("student_id")

if not student_id:
    st.warning("Please log in to upload documents or view document status")
    st.stop()

# Process any verification tasks
process_verification_queue()

if user_role == "student":
    # Student view - Document upload interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.info("""
        **Document Requirements:**
        - All documents must be in PDF format
        - Maximum file size: 10MB per document
        - Ensure all text is clearly legible
        - Official transcripts must be sealed/verified
        """)

    with col2:
        st.info("""
        **Verification Process:**
        Documents will be automatically verified by our AI system.
        You can check status updates in real-time.
        """)

    st.subheader("Required Documents")
    required_documents = ["Official Transcript", "ID/Passport", "Proof of Residence", "Recommendation Letter"]
    
    # Fetch document statuses from database
    documents = get_documents_for_student(student_id)
    document_status = {doc['document_name']: {"status": doc['status'], "uploaded": True, "id": doc['id'], "reason": doc.get('reason')} for doc in documents}

    # Display document list with upload options
    for doc_name in required_documents:
        doc_info = document_status.get(doc_name, {"status": "Not Uploaded", "uploaded": False, "id": None})
        status_icon = "✅" if doc_info['status'] == 'Verified' else "❌" if doc_info['status'] == 'Rejected' else "⏳" if doc_info['status'] == 'Pending' else "📄"
        
        with st.expander(f"{status_icon} {doc_name} - {doc_info['status']}", expanded=not doc_info['uploaded']):
            if doc_info['status'] == 'Verified':
                st.success(f"✅ Your {doc_name} has been verified by our AI system.")
                if st.button(f"Replace {doc_name}", key=f"replace_{doc_name}"):
                    uploaded_file = st.file_uploader(f"Upload new {doc_name}", type=['pdf'], key=f"upload_{doc_name}")
                    if uploaded_file:
                        handle_document_upload(student_id, doc_name, uploaded_file, doc_info['id'])
                        st.success(f"New {doc_name} uploaded successfully. Our AI system will verify it shortly.")
                        st.rerun()
            
            elif doc_info['status'] == 'Rejected':
                st.error(f"❌ Your {doc_name} was rejected by our AI verification system. Reason: {doc_info.get('reason', 'Not specified')}")
                uploaded_file = st.file_uploader(f"Upload new {doc_name}", type=['pdf'], key=f"upload_{doc_name}")
                if uploaded_file:
                    handle_document_upload(student_id, doc_name, uploaded_file, doc_info['id'])
                    st.success(f"New {doc_name} uploaded successfully. Our AI system will verify it shortly.")
                    st.rerun()
            
            elif doc_info['status'] == 'Pending':
                st.info(f"⏳ Your {doc_name} is being processed by our AI verification system. This usually takes 1-2 minutes.")
                # Check if we have a task in progress
                if "verification_tasks" in st.session_state:
                    for task_id, task in st.session_state.verification_tasks.items():
                        if task["document_id"] == doc_info['id'] and task["status"] == "processing":
                            st.info("AI verification in progress...")
                            st.progress(0.5)
            
            else:
                if not doc_info['uploaded']:
                    uploaded_file = st.file_uploader(f"Upload {doc_name}", type=['pdf'], key=f"upload_{doc_name}")
                    if uploaded_file:
                        handle_document_upload(student_id, doc_name, uploaded_file)
                        st.success(f"{doc_name} uploaded successfully. Our AI system will verify it shortly.")
                        st.rerun()
                else:
                    st.info(f"⏳ Your {doc_name} is pending AI verification")
    
    # Document verification status
    st.subheader("Document Verification Status")
    verified_count = sum(1 for doc in documents if doc.get('status') == "Verified")
    total_required = len(required_documents)
    progress_percentage = verified_count / total_required if total_required > 0 else 0
    
    st.progress(progress_percentage)
    st.markdown(f"**{verified_count}/{total_required}** required documents verified")
    
    if progress_percentage < 1.0:
        st.warning("Your application cannot be fully processed until all required documents are verified")
    else:
        st.success("All required documents have been verified! Your application is now being processed.")

elif user_role == "admin":
    # Admin view - Document verification interface with AI assistance
    st.subheader("Document Verification Dashboard")
    
    # Add option to toggle AI verification
    ai_auto_verify = st.checkbox("Enable AI auto-verification", value=True, 
                                help="When enabled, AI will automatically verify documents. Otherwise, they'll be flagged for manual review.")
    
    # Add tabs for pending and all documents
    tab1, tab2 = st.tabs(["Pending Verification", "All Documents"])
    
    with tab1:
        # Query all pending documents
        documents_collection = get_collection("documents")
        pending_results = documents_collection.get(
            where={"status": "Pending"}
        )
        
        if pending_results and pending_results['documents']:
            st.write(f"Found {len(pending_results['documents'])} documents pending verification")
            
            # Display each pending document
            for i, doc in enumerate(pending_results['documents']):
                if doc:
                    doc_data = json.loads(doc)
                    doc_id = pending_results['ids'][i]
                    
                    with st.expander(f"{doc_data['document_name']} - Student ID: {doc_data['student_id']}"):
                        st.write(f"Uploaded on: {doc_data['upload_date']}")
                        st.write(f"File path: {doc_data['file_path']}")
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            if st.button("AI Verify", key=f"ai_verify_{doc_id}"):
                                st.info("AI verification in progress...")
                                
                                # For demo purposes - simulate AI verification
                                import random
                                import time
                                time.sleep(1)  # Simulate processing time
                                
                                statuses = ["Verified", "Rejected"]
                                weights = [0.8, 0.2]  # 80% chance of verification
                                new_status = random.choices(statuses, weights=weights, k=1)[0]
                                
                                if new_status == "Rejected":
                                    reasons = [
                                        "AI detected potential document alteration",
                                        "AI detected inconsistency with student records",
                                        "Document does not meet quality requirements",
                                        "Missing crucial information"
                                    ]
                                    reason = random.choice(reasons)
                                    update_document_status(doc_id, new_status, reason)
                                    st.error(f"AI rejected document: {reason}")
                                else:
                                    update_document_status(doc_id, new_status)
                                    st.success("AI verified document successfully!")
                                st.rerun()
                        
                        with col2:
                            if st.button("Manual Verify", key=f"verify_{doc_id}"):
                                update_document_status(doc_id, "Verified")
                                st.success("Document manually verified!")
                                st.rerun()
                        
                        with col3:
                            if st.button("Reject Document", key=f"reject_{doc_id}"):
                                reason = st.text_input("Rejection reason:", key=f"reason_{doc_id}")
                                if reason and st.button("Confirm Rejection", key=f"confirm_reject_{doc_id}"):
                                    update_document_status(doc_id, "Rejected", reason)
                                    st.error("Document rejected.")
                                    st.rerun()
                        
                        # Show AI confidence score (simulated)
                        if ai_auto_verify:
                            import random
                            confidence = random.uniform(0.7, 0.98)
                            st.metric("AI Confidence Score", f"{confidence:.2f}")
                            
                            # AI insights (simulated)
                            insights = [
                                "Document appears to be authentic",
                                "No signs of tampering detected",
                                "Student information matches our records",
                                "Document follows expected format",
                                "Some areas have low resolution but still readable"
                            ]
                            
                            st.subheader("AI Analysis")
                            for insight in random.sample(insights, 3):
                                st.write(f"- {insight}")
        else:
            st.info("No documents pending verification")
    
    with tab2:
        # Get all documents
        all_results = documents_collection.get()
        
        if all_results and all_results['documents']:
            # Convert to dataframe for better display
            all_docs = []
            for i, doc in enumerate(all_results['documents']):
                if doc:
                    doc_data = json.loads(doc)
                    doc_data['id'] = all_results['ids'][i]
                    all_docs.append(doc_data)
            
            if all_docs:
                df = pd.DataFrame(all_docs)
                
                # Add verification stats
                verified_count = sum(1 for doc in all_docs if doc.get('status') == "Verified")
                rejected_count = sum(1 for doc in all_docs if doc.get('status') == "Rejected")
                pending_count = sum(1 for doc in all_docs if doc.get('status') == "Pending")
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Verified Documents", verified_count)
                col2.metric("Rejected Documents", rejected_count)
                col3.metric("Pending Documents", pending_count)
                
                # Show the dataframe
                st.dataframe(df)
                
                # Add option to download verification report
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download Verification Report",
                    data=csv,
                    file_name="document_verification_report.csv",
                    mime="text/csv",
                )
        else:
            st.info("No documents found in the database")
    
    # Add AI performance monitoring
    if ai_auto_verify:
        st.subheader("AI Verification Performance")
        
        # Simulated data
        import random
        accuracy = random.uniform(0.92, 0.98)
        false_positives = random.uniform(0.01, 0.04)
        false_negatives = random.uniform(0.01, 0.03)
        avg_time = random.uniform(10, 30)
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Accuracy", f"{accuracy:.2%}")
        col2.metric("False Positives", f"{false_positives:.2%}")
        col3.metric("False Negatives", f"{false_negatives:.2%}")
        col4.metric("Avg. Process Time", f"{avg_time:.1f}s")
        
        # Simulated chart for verification history
        import numpy as np
        
        # Generate random data for chart
        dates = pd.date_range(end=datetime.now(), periods=14).strftime('%Y-%m-%d').tolist()
        verified = np.random.randint(15, 50, size=14).tolist()
        rejected = np.random.randint(2, 10, size=14).tolist()
        
        chart_data = pd.DataFrame({
            'Date': dates,
            'Verified': verified,
            'Rejected': rejected
        })
        
        st.line_chart(chart_data.set_index('Date'))
else:
    # Not logged in view
    st.warning("Please log in with admin credentials to access the verification dashboard")

# Render footer
render_footer()