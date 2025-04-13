from crewai import Agent, Task
from langchain.llms import HuggingFaceHub
from typing import Dict, List, Any
import os
from datetime import datetime

# Import database client
from ..database.chroma_client import add_document, get_document, query_documents, update_document, delete_document
class StudentCounsellorAgent:
    def __init__(self):
        # Initialize the language model
        self.llm = HuggingFaceHub(
            repo_id="mistralai/Mistral-7B-Instruct-v0.2",
            model_kwargs={"temperature": 0.7, "max_length": 1024}
        )
        
        # Create the agent
        self.agent = Agent(
            role="Student Counsellor",
            goal="Communicate effectively with students at various stages of the admission process",
            backstory="Empathetic counsellor with excellent communication skills and deep understanding of student needs and concerns.",
            verbose=True,
            llm=self.llm
        )
    
    def create_task(self, task_type: str, context_id: str) -> Task:
        """Create a communication task"""
        if task_type == "welcome_message":
            return Task(
                description=f"Create a welcoming message for student {context_id}",
                agent=self.agent,
                expected_output="Personalized welcome message for the student"
            )
        elif task_type == "document_request":
            return Task(
                description=f"Request missing documents for admission {context_id}",
                agent=self.agent,
                expected_output="Clear document request message"
            )
        elif task_type == "status_update":
            return Task(
                description=f"Provide status update for admission {context_id}",
                agent=self.agent,
                expected_output="Informative status update message"
            )
        elif task_type == "admission_letter":
            return Task(
                description=f"Generate admission letter for admission {context_id}",
                agent=self.agent,
                expected_output="Official admission letter with all necessary details"
            )
        elif task_type == "rejection_letter":
            return Task(
                description=f"Generate rejection letter for admission {context_id}",
                agent=self.agent,
                expected_output="Empathetic rejection letter with alternatives or guidance"
            )
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    
    async def send_welcome_message(self, student_id: str) -> Dict[str, Any]:
        """Send a welcome message to a new student"""
        # Get the student information
        student = get_document("students", student_id)
        if not student:
            raise ValueError(f"Student {student_id} not found")
        
        # Create a task for the agent
        task = self.create_task("welcome_message", student_id)
        
        # Execute the task
        result = await task.execute(
            context={
                "student": student
            }
        )
        
        # Record the communication
        communication = {
            "student_id": student_id,
            "type": "welcome_message",
            "content": result,
            "date": str(datetime.now()),
            "sent_by": "Student Counsellor Agent"
        }
        
        comm_id = add_document("communications", communication, f"comm_{datetime.now().timestamp()}")
        
        # Update student with communication ID
        if "communications" not in student:
            student["communications"] = []
        
        student["communications"].append(comm_id)
        update_document("students", student_id, student)
        
        return {
            "student_id": student_id,
            "message": result,
            "communication_id": comm_id
        }
    
    async def request_missing_documents(self, admission_id: str) -> Dict[str, Any]:
        """Request missing documents for an admission application"""
        # Get the admission application
        admission = get_document("admissions", admission_id)
        if not admission:
            raise ValueError(f"Admission application {admission_id} not found")
        
        # Get the student information
        student = get_document("students", admission["student_id"])
        if not student:
            raise ValueError(f"Student {admission['student_id']} not found")
        
        # Get missing documents
        from agents.document_checker import DocumentCheckerAgent
        doc_checker = DocumentCheckerAgent()
        missing_docs = await doc_checker.check_missing_documents(admission_id)
        
        # Create a task for the agent
        task = self.create_task("document_request", admission_id)
        
        # Execute the task
        result = await task.execute(
            context={
                "student": student,
                "admission": admission,
                "missing_documents": missing_docs
            }
        )
        
        # Record the communication
        communication = {
            "student_id": student["id"],
            "admission_id": admission_id,
            "type": "document_request",
            "content": result,
            "date": str(datetime.now()),
            "sent_by": "Student Counsellor Agent",
            "missing_documents": missing_docs
        }
        
        comm_id = add_document("communications", communication, f"comm_{datetime.now().timestamp()}")
        
        # Update admission with communication
        if "communication_history" not in admission:
            admission["communication_history"] = []
        
        admission["communication_history"].append({
            "date": str(datetime.now()),
            "type": "document_request",
            "communication_id": comm_id
        })
        
        update_document("admissions", admission_id, admission)
        
        return {
            "admission_id": admission_id,
            "student_id": student["id"],
            "message": result,
            "missing_documents": missing_docs,
            "communication_id": comm_id
        }
    
    async def send_status_update(self, admission_id: str) -> Dict[str, Any]:
        """Send a status update for an admission application"""
        # Get the admission application
        admission = get_document("admissions", admission_id)
        if not admission:
            raise ValueError(f"Admission application {admission_id} not found")
        
        # Get the student information
        student = get_document("students", admission["student_id"])
        if not student:
            raise ValueError(f"Student {admission['student_id']} not found")
        
        # Create a task for the agent
        task = self.create_task("status_update", admission_id)
        
        # Execute the task
        result = await task.execute(
            context={
                "student": student,
                "admission": admission,
                "status": admission["status"]
            }
        )
        
        # Record the communication
        communication = {
            "student_id": student["id"],
            "admission_id": admission_id,
            "type": "status_update",
            "content": result,
            "date": str(datetime.now()),
            "sent_by": "Student Counsellor Agent"
        }
        
        comm_id = add_document("communications", communication, f"comm_{datetime.now().timestamp()}")
        
        # Update admission with communication
        if "communication_history" not in admission:
            admission["communication_history"] = []
        
        admission["communication_history"].append({
            "date": str(datetime.now()),
            "type": "status_update",
            "communication_id": comm_id
        })
        
        update_document("admissions", admission_id, admission)
        
        return {
            "admission_id": admission_id,
            "student_id": student["id"],
            "message": result,
            "communication_id": comm_id
        }
    
    async def send_admission_letter(self, admission_id: str) -> Dict[str, Any]:
        """Send an admission letter for an accepted application"""
        # Get the admission application
        admission = get_document("admissions", admission_id)
        if not admission:
            raise ValueError(f"Admission application {admission_id} not found")
        
        # Check if application is accepted
        if admission["status"] != "accepted":
            raise ValueError(f"Admission application {admission_id} is not accepted")
        
        # Get the student information
        student = get_document("students", admission["student_id"])
        if not student:
            raise ValueError(f"Student {admission['student_id']} not found")
        
        # Get fee structure
        fee_structure = query_documents("fee_structure", admission["program"])
        
        # Create a task for the agent
        task = self.create_task("admission_letter", admission_id)
        
        # Execute the task
        result = await task.execute(
            context={
                "student": student,
                "admission": admission,
                "program": admission["program"],
                "fee_structure": fee_structure[0] if fee_structure else {}
            }
        )
        
        # Record the communication
        communication = {
            "student_id": student["id"],
            "admission_id": admission_id,
            "type": "admission_letter",
            "content": result,
            "date": str(datetime.now()),
            "sent_by": "Student Counsellor Agent"
        }
        
        comm_id = add_document("communications", communication, f"comm_{datetime.now().timestamp()}")
        
        # Update admission with communication and letter status
        if "communication_history" not in admission:
            admission["communication_history"] = []
        
        admission["communication_history"].append({
            "date": str(datetime.now()),
            "type": "admission_letter",
            "communication_id": comm_id
        })
        
        admission["admission_letter_sent"] = True
        update_document("admissions", admission_id, admission)
        
        return {
            "admission_id": admission_id,
            "student_id": student["id"],
            "letter": result,
            "communication_id": comm_id
        }
    
    async def send_rejection_letter(self, admission_id: str) -> Dict[str, Any]:
        """Send a rejection letter for a rejected application"""
        # Get the admission application
        admission = get_document("admissions", admission_id)
        if not admission:
            raise ValueError(f"Admission application {admission_id} not found")
        
        # Check if application is rejected
        if admission["status"] != "rejected":
            raise ValueError(f"Admission application {admission_id} is not rejected")
        
        # Get the student information
        student = get_document("students", admission["student_id"])
        if not student:
            raise ValueError(f"Student {admission['student_id']} not found")
        
        # Create a task for the agent
        task = self.create_task("rejection_letter", admission_id)
        
        # Execute the task
        result = await task.execute(
            context={
                "student": student,
                "admission": admission,
                "program": admission["program"],
                "shortlisting_results": admission.get("shortlisting_results", {})
            }
        )
        
        # Record the communication
        communication = {
            "student_id": student["id"],
            "admission_id": admission_id,
            "type": "rejection_letter",
            "content": result,
            "date": str(datetime.now()),
            "sent_by": "Student Counsellor Agent"
        }
        
        comm_id = add_document("communications", communication, f"comm_{datetime.now().timestamp()}")
        
        # Update admission with communication
        if "communication_history" not in admission:
            admission["communication_history"] = []
        
        admission["communication_history"].append({
            "date": str(datetime.now()),
            "type": "rejection_letter",
            "communication_id": comm_id
        })
        
        update_document("admissions", admission_id, admission)
        
        return {
            "admission_id": admission_id,
            "student_id": student["id"],
            "letter": result,
            "communication_id": comm_id
        }