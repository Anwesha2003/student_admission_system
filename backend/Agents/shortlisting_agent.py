from crewai import Agent, Task
from langchain.llms import HuggingFaceHub
from typing import Dict, List, Any
import os
from datetime import datetime
from typing_extensions import Self

# Import database client
from ..database.chroma_client import get_client, get_collection, initialize_chroma_db, get_document, query_documents, update_document

class ShortlistingAgent:
    def __init__(self):
        # Initialize the language model
        self.llm = HuggingFaceHub(
            repo_id="mistralai/Mistral-7B-Instruct-v0.2",
            model_kwargs={"temperature": 0.5, "max_length": 1024}
        )
        
        # Create the agent
        self.agent = Agent(
            role="Shortlisting Agent",
            goal="Evaluate applications based on eligibility criteria and university capacity",
            backstory="Analytical evaluator with extensive experience in selecting the best candidates based on multiple criteria.",
            verbose=True,
            llm=self.llm
        )
        
        # Ensure database is initialized
        initialize_chroma_db()
    
    def create_task(self, document_id: str) -> Task:
        """Create a shortlisting task"""
        return Task(
            description=f"Evaluate admission application {document_id} based on eligibility criteria and university capacity",
            agent=self.agent,
            expected_output="Comprehensive evaluation with scoring and recommendation"
        )
    
    async def evaluate_application(self, document_id: str) -> Dict[str, Any]:
        """Evaluate an admission application for shortlisting"""
        # Get the admission application
        admission = get_document("admissions", document_id)
        if not admission:
            raise ValueError(f"Admission application {document_id} not found")
        
        # Check if the application is ready for shortlisting
        if admission["status"] != "shortlisted" and admission["status"] != "document_verification":
            raise ValueError(f"Admission application {document_id} is not ready for shortlisting")
        
        # Get the student information
        student = get_document("students", admission["student_id"])
        if not student:
            raise ValueError(f"Student {admission['student_id']} not found")
        
        # Get the program requirements
        program_requirements = query_documents("eligibility_criteria", admission["program"])
        if not program_requirements:
            raise ValueError(f"No eligibility criteria found for program {admission['program']}")
        
        # Create a task for the agent
        task = self.create_task(document_id)
        
        # Execute the task
        result = await task.execute(
            context={
                "admission": admission,
                "student": student,
                "program_requirements": program_requirements[0] if program_requirements else {},
                "verification_results": admission.get("verification_results", {})
            }
        )
        
        # Parse the result to extract scores and recommendation
        lines = result.split('\n')
        scores = {}
        recommendation = ""
        
        for line in lines:
            if ':' in line and not line.startswith('Recommendation'):
                key, value = line.split(':', 1)
                try:
                    scores[key.strip()] = float(value.strip())
                except ValueError:
                    scores[key.strip()] = value.strip()
            if line.startswith('Recommendation'):
                recommendation = line.split(':', 1)[1].strip()
        
        # Calculate overall score
        overall_score = 0
        score_count = 0
        for key, value in scores.items():
            if isinstance(value, (int, float)):
                overall_score += value
                score_count += 1
        
        if score_count > 0:
            overall_score = overall_score / score_count
        
        # Update the admission with the shortlisting results
        admission["shortlisting_results"] = {
            "scores": scores,
            "overall_score": overall_score,
            "recommendation": recommendation,
            "evaluation": result,
            "date": str(datetime.now())
        }
        
        # Update status based on recommendation
        if "recommend" in recommendation.lower() and "not" not in recommendation.lower():
            admission["status"] = "accepted"
        else:
            admission["status"] = "rejected"
        
        update_document("admissions", document_id, admission)
        
        return admission
    
    async def batch_evaluate(self, program: str = None) -> Dict[str, Any]:
        """Evaluate all applications for a program that are ready for shortlisting"""
        # Get all applications ready for shortlisting
        query_filter = {"status": "shortlisted"}
        if program:
            query_filter["program"] = program
        
        applications = query_documents("admissions", "", metadata_filter=query_filter)
        
        results = {}
        for application in applications:
            try:
                result = await self.evaluate_application(application["id"])
                results[application["id"]] = {
                    "status": result["status"],
                    "overall_score": result["shortlisting_results"]["overall_score"],
                    "recommendation": result["shortlisting_results"]["recommendation"]
                }
            except Exception as e:
                results[application["id"]] = {
                    "error": str(e)
                }
        
        return {
            "program": program,
            "evaluated_count": len(results),
            "results": results
        }
    
    async def evaluate_capacity(self, program: str) -> Dict[str, Any]:
        """Evaluate university capacity for a program"""
        # Get program capacity from static documents
        program_info = query_documents("eligibility_criteria", program)
        
        if not program_info:
            raise ValueError(f"No information found for program {program}")
        
        program_capacity = program_info[0].get("capacity", 100)  # Default capacity if not specified
        
        # Get accepted applications count
        accepted_applications = query_documents("admissions", "", metadata_filter={"program": program, "status": "accepted"})
        accepted_count = len(accepted_applications)
        
        # Get pending applications count
        pending_applications = query_documents("admissions", "", metadata_filter={"program": program, "status": "shortlisted"})
        pending_count = len(pending_applications)
        
        # Create a task for the agent
        task = Task(
            description=f"Evaluate capacity for program {program}",
            agent=self.agent,
            expected_output="Capacity analysis and recommendations"
        )
        
        # Execute the task
        result = await task.execute(
            context={
                "program": program,
                "program_capacity": program_capacity,
                "accepted_count": accepted_count,
                "pending_count": pending_count
            }
        )
        
        return {
            "program": program,
            "capacity": program_capacity,
            "accepted_count": accepted_count,
            "pending_count": pending_count,
            "available_slots": max(0, program_capacity - accepted_count),
            "analysis": result
        }