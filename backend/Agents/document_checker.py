from crewai import Agent, Task
from langchain.llms import HuggingFaceHub
from typing import Dict, List, Any
import os
from datetime import datetime
from typing_extensions import Self


# Import database client
from ..database.chroma_client import get_client,get_collection,initialize_chroma_db,get_document, update_document, query_documents

class DocumentCheckerAgent:
    def __init__(self):
        # Initialize the language model
        self.llm = HuggingFaceHub(
            repo_id="mistralai/Mistral-7B-Instruct-v0.2",
            model_kwargs={"temperature": 0.3, "max_length": 1024}
        )
        
        # Create the agent
        self.agent = Agent(
            role="Document Checker",
            goal="Validate submitted applications and check documents for authenticity and completeness",
            backstory="Detail-oriented document verification specialist with experience in spotting inconsistencies and verifying authenticity.",
            verbose=True,
            llm=self.llm
        )
    
    def create_task(self, document_id: str) -> Task:
        """Create a document verification task"""
        return Task(
            description=f"Verify document {document_id} for authenticity and completeness",
            agent=self.agent,
            expected_output="Verification report with status and notes"
        )
    
    async def verify_document(self, document_id: str) -> Dict[str, Any]:
        """Verify a document"""
        # Get the document
        document = get_document("documents", document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        # Get the admission application
        admission = get_document("admissions", document["document_id"])
        if not admission:
            raise ValueError(f"Admission application {document['document_id']} not found")
        
        # Get the student information
        student = get_document("students", document["student_id"])
        if not student:
            raise ValueError(f"Student {document['student_id']} not found")
        
        # Create a task for the agent
        task = self.create_task(document_id)
        
        # Execute the task
        result = await task.execute(
            context={
                "document": document,
                "admission": admission,
                "student": student
            }
        )
        
        # Parse the result
        verification_status = "verified"
        verification_notes = result
        
        if "inconsistency" in result.lower() or "issue" in result.lower() or "problem" in result.lower():
            verification_status = "needs_clarification"
        
        if "reject" in result.lower() or "invalid" in result.lower() or "fake" in result.lower():
            verification_status = "rejected"
        
        # Update the document with verification results
        document["verification_status"] = verification_status
        document["verification_date"] = str(datetime.now())
        document["verification_notes"] = verification_notes
        update_document("documents", document_id, document)
        
        # Update the admission application
        if "verification_results" not in admission:
            admission["verification_results"] = {}
        
        admission["verification_results"][document["document_type"]] = {
            "status": verification_status,
            "notes": verification_notes,
            "date": str(datetime.now())
        }
        
        # Update the admission status if all documents are verified
        required_documents = ["transcript", "id_proof", "recommendation_letter"]
        all_verified = True
        
        for doc_type in required_documents:
            if doc_type not in admission["verification_results"] or admission["verification_results"][doc_type]["status"] != "verified":
                all_verified = False
                break
        
        if all_verified and admission["status"] == "document_verification":
            admission["status"] = "shortlisted"
        
        update_document("admissions", document["document_id"], admission)
        
        return document
    
    async def verify_all_documents(self, document_id: str) -> Dict[str, Any]:
        """Verify all documents for an admission application"""
        # Get the admission application
        admission = get_document("admissions", document_id)
        if not admission:
            raise ValueError(f"Admission application {document_id} not found")
        
        # Update admission status to document verification
        admission["status"] = "document_verification"
        update_document("admissions", document_id, admission)
        
        # Get all documents for this admission
        documents = query_documents("documents", "", metadata_filter={"document_id": document_id})
        
        results = {}
        for document in documents:
            doc_result = await self.verify_document(document["id"])
            results[document["document_type"]] = doc_result
        
        return {
            "document_id": document_id,
            "verification_results": results
        }
    
    async def check_missing_documents(self, document_id: str) -> List[str]:
        """Check for missing required documents"""
        # Get the admission application
        admission = get_document("admissions", document_id)
        if not admission:
            raise ValueError(f"Admission application {document_id} not found")
        
        # Get all documents for this admission
        documents = query_documents("documents", "", metadata_filter={"document_id": document_id})
        
        # Get document types
        document_types = [doc["document_type"] for doc in documents]
        
        # Check for required documents
        required_documents = ["transcript", "id_proof", "recommendation_letter"]
        missing_documents = [doc for doc in required_documents if doc not in document_types]
        
        return missing_documents