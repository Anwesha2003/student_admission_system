from crewai import Agent, Task
from langchain.llms import HuggingFaceHub
from typing import Dict, List, Any
import os
from datetime import datetime
from typing_extensions import Self

# Import database client
from ..database.chroma_client import get_client,get_collection,initialize_chroma_db,get_document, query_documents, update_document

class AdmissionOfficerAgent:
    def __init__(self):
        # Initialize the language model
        self.llm = HuggingFaceHub(
            repo_id="mistralai/Mistral-7B-Instruct-v0.2",
            model_kwargs={"temperature": 0.7, "max_length": 1024}
        )
        
        # Create the agent
        self.agent = Agent(
            role="Admission Officer",
            goal="Oversee the admission process and make final decisions",
            backstory="Experienced admission officer with expertise in evaluating applications and making informed decisions.",
            verbose=True,
            llm=self.llm
        )
    
    def create_task(self, admission_id: str, task_type: str) -> Task:
        """Create a task for the admission officer"""
        if task_type == "review_application":
            return Task(
                description=f"Review the admission application {admission_id} and coordinate with other agents",
                agent=self.agent,
                expected_output="Comprehensive review and decision for the application"
            )
        elif task_type == "make_decision":
            return Task(
                description=f"Make a final decision on admission application {admission_id} based on all available information",
                agent=self.agent,
                expected_output="Final admission decision with justification"
            )
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    
    async def review_application(self, admission_id: str) -> Dict[str, Any]:
        """Review an admission application"""
        # Get the admission application
        admission = get_document("admissions", admission_id)
        if not admission:
            raise ValueError(f"Admission application {admission_id} not found")
        
        # Get the student information
        student = get_document("students", admission["student_id"])
        if not student:
            raise ValueError(f"Student {admission['student_id']} not found")
        
        # Get the documents
        documents = query_documents("documents", "", metadata_filter={"admission_id": admission_id})
        
        # Get the program requirements
        program_requirements = query_documents("eligibility_criteria", admission["program"])
        
        # Create a task for the agent
        task = self.create_task(admission_id, "review_application")
        
        # Execute the task
        result = await task.execute(
            context={
                "admission": admission,
                "student": student,
                "documents": documents,
                "program_requirements": program_requirements
            }
        )
        
        # Update the admission with the review results
        admission["officer_review"] = {
            "result": result,
            "date": str(datetime.now())
        }
        update_document("admissions", admission_id, admission)
        
        return admission
    
    async def make_decision(self, admission_id: str) -> Dict[str, Any]:
        """Make a final decision on an admission application"""
        # Get the admission application
        admission = get_document("admissions", admission_id)
        if not admission:
            raise ValueError(f"Admission application {admission_id} not found")
        
        # Check if all required steps are completed
        if "verification_results" not in admission or "shortlisting_results" not in admission:
            raise ValueError(f"Admission application {admission_id} is not ready for decision")
        
        # Create a task for the agent
        task = self.create_task(admission_id, "make_decision")
        
        # Execute the task
        result = await task.execute(
            context={
                "admission": admission,
                "verification_results": admission["verification_results"],
                "shortlisting_results": admission["shortlisting_results"]
            }
        )
        
        # Update the admission with the decision
        admission["status"] = "accepted" if "accepted" in result.lower() else "rejected"
        admission["decision"] = {
            "result": result,
            "date": str(datetime.now())
        }
        update_document("admissions", admission_id, admission)
        
        return admission
    
    async def get_status_update(self, admission_id: str = None) -> str:
        """Get a status update for the admission process"""
        if admission_id:
            # Get status of a specific admission
            admission = get_document("admissions", admission_id)
            if not admission:
                return f"Admission application {admission_id} not found"
            
            # Create a task for the agent
            task = Task(
                description=f"Provide a status update for admission application {admission_id}",
                agent=self.agent,
                expected_output="Detailed status update for the application"
            )
            
            # Execute the task
            result = await task.execute(
                context={
                    "admission": admission
                }
            )
            
            return result
        else:
            # Get overall status of the admission process
            # Count applications by status
            pending_count = len(query_documents("admissions", "", metadata_filter={"status": "pending"}))
            verification_count = len(query_documents("admissions", "", metadata_filter={"status": "document_verification"}))
            shortlisted_count = len(query_documents("admissions", "", metadata_filter={"status": "shortlisted"}))
            accepted_count = len(query_documents("admissions", "", metadata_filter={"status": "accepted"}))
            rejected_count = len(query_documents("admissions", "", metadata_filter={"status": "rejected"}))
            enrolled_count = len(query_documents("admissions", "", metadata_filter={"status": "enrolled"}))
            
            # Create a task for the agent
            task = Task(
                description="Provide an overall status update for the admission process",
                agent=self.agent,
                expected_output="Comprehensive status report for the admission process"
            )
            
            # Execute the task
            result = await task.execute(
                context={
                    "stats": {
                        "pending": pending_count,
                        "verification": verification_count,
                        "shortlisted": shortlisted_count,
                        "accepted": accepted_count,
                        "rejected": rejected_count,
                        "enrolled": enrolled_count
                    }
                }
            )
            
            return result