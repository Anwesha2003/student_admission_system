"""
Loan Agent module responsible for processing student loan applications,
performing preliminary qualification checks, and providing loan recommendations.
"""
import logging
from typing import Dict, List, Optional, Tuple

from ..models.loan import LoanApplication, LoanStatus, LoanType
from ..models.student import Student
from ..utils.helpers import calculate_loan_eligibility_score

# Set up logging
logger = logging.getLogger(__name__)

class LoanAgent:
    """
    AI agent that processes loan applications and provides recommendations.
    """
    
    def __init__(self):
        """Initialize the loan agent with default parameters."""
        self.min_eligibility_score = 60  # Minimum score to qualify for loans
        self.interest_rates = {
            LoanType.FEDERAL: 4.99,
            LoanType.PRIVATE: 6.5,
            LoanType.SCHOLARSHIP_BACKED: 3.75,
            LoanType.INCOME_SHARE: 0.0  # No interest but percentage of future income
        }
        logger.info("Loan agent initialized")
    
    async def process_application(self, application: LoanApplication, student: Student) -> Dict:
        """
        Process a loan application and determine eligibility.
        
        Args:
            application: The loan application to process
            student: The student applying for the loan
            
        Returns:
            Dictionary containing processing results and recommendations
        """
        logger.info(f"Processing loan application for student {student.id}")
        
        # Calculate eligibility score based on multiple factors
        eligibility_score = await self._calculate_eligibility(application, student)
        
        # Determine qualification status
        qualified = eligibility_score >= self.min_eligibility_score
        
        # Generate appropriate loan options if qualified
        loan_options = []
        if qualified:
            loan_options = await self._generate_loan_options(application, student, eligibility_score)
            
        # Update application status
        status = LoanStatus.PENDING_REVIEW if qualified else LoanStatus.NEEDS_INFORMATION
        
        return {
            "application_id": application.id,
            "student_id": student.id,
            "eligibility_score": eligibility_score,
            "qualified": qualified,
            "status": status,
            "loan_options": loan_options,
            "feedback": await self._generate_feedback(application, student, eligibility_score)
        }
    
    async def _calculate_eligibility(self, application: LoanApplication, student: Student) -> float:
        """
        Calculate loan eligibility score based on application details and student profile.
        
        Args:
            application: The loan application
            student: The student profile
            
        Returns:
            Eligibility score between 0-100
        """
        # Use utility function for core calculation
        base_score = calculate_loan_eligibility_score(application, student)
        
        # Apply additional factors like program type and academic standing
        adjustments = 0
        
        # Adjustment based on academic performance
        if hasattr(student, 'gpa') and student.gpa:
            if student.gpa >= 3.7:
                adjustments += 10
            elif student.gpa >= 3.0:
                adjustments += 5
        
        # Adjustment based on selected program's employment outcomes
        if hasattr(application, 'program') and application.program:
            # This would typically connect to a database of program statistics
            # Simplified here with a hypothetical check
            high_demand_programs = ["Computer Science", "Nursing", "Engineering"]
            if application.program in high_demand_programs:
                adjustments += 5
        
        return min(100, max(0, base_score + adjustments))
    
    async def _generate_loan_options(
        self, 
        application: LoanApplication, 
        student: Student, 
        score: float
    ) -> List[Dict]:
        """
        Generate appropriate loan options based on eligibility score.
        
        Args:
            application: The loan application
            student: The student profile
            score: The calculated eligibility score
            
        Returns:
            List of loan options with terms and conditions
        """
        options = []
        requested_amount = application.requested_amount
        
        # Federal loan option - available to most qualified applicants
        if score >= 60:
            options.append({
                "type": LoanType.FEDERAL,
                "amount": min(requested_amount, 20000),  # Federal loans often have caps
                "interest_rate": self.interest_rates[LoanType.FEDERAL],
                "term_years": 10,
                "monthly_payment": self._calculate_monthly_payment(
                    min(requested_amount, 20000), 
                    self.interest_rates[LoanType.FEDERAL], 
                    10
                )
            })
        
        # Private loan option - higher score requirements
        if score >= 70:
            options.append({
                "type": LoanType.PRIVATE,
                "amount": requested_amount,
                "interest_rate": self.interest_rates[LoanType.PRIVATE],
                "term_years": 15,
                "monthly_payment": self._calculate_monthly_payment(
                    requested_amount, 
                    self.interest_rates[LoanType.PRIVATE], 
                    15
                )
            })
        
        # Scholarship-backed loans for high scorers
        if score >= 85:
            options.append({
                "type": LoanType.SCHOLARSHIP_BACKED,
                "amount": min(requested_amount, 15000),
                "interest_rate": self.interest_rates[LoanType.SCHOLARSHIP_BACKED],
                "term_years": 10,
                "monthly_payment": self._calculate_monthly_payment(
                    min(requested_amount, 15000), 
                    self.interest_rates[LoanType.SCHOLARSHIP_BACKED], 
                    10
                )
            })
        
        # Income Share Agreement option for specific programs
        if hasattr(application, 'program') and application.program in [
            "Computer Science", "Data Science", "Software Engineering"
        ]:
            options.append({
                "type": LoanType.INCOME_SHARE,
                "amount": requested_amount,
                "interest_rate": self.interest_rates[LoanType.INCOME_SHARE],
                "term_years": 5,
                "income_percentage": 12,
                "details": "Pay 12% of your income for 5 years after graduation"
            })
        
        return options
    
    async def _generate_feedback(
        self, 
        application: LoanApplication, 
        student: Student, 
        score: float
    ) -> str:
        """
        Generate helpful feedback for the student based on their application.
        
        Args:
            application: The loan application
            student: The student profile
            score: The calculated eligibility score
            
        Returns:
            Feedback string with suggestions or next steps
        """
        if score >= 85:
            return "Your application looks strong. You qualify for our best loan options."
        elif score >= 70:
            return "You qualify for most loan options. Consider providing additional income verification to potentially improve terms."
        elif score >= 60:
            return "You qualify for basic loan options. Consider adding a co-signer to improve your terms."
        else:
            missing_items = []
            if not application.income_verification:
                missing_items.append("income verification")
            if not application.credit_score or application.credit_score < 600:
                missing_items.append("acceptable credit score")
            if not application.cosigner and score < 50:
                missing_items.append("co-signer")
                
            feedback = "Your application needs improvement. "
            if missing_items:
                feedback += f"Please provide: {', '.join(missing_items)}."
            else:
                feedback += "Please review your application details for accuracy."
            
            return feedback
    
    def _calculate_monthly_payment(self, principal: float, rate: float, years: int) -> float:
        """
        Calculate estimated monthly payment for a loan.
        
        Args:
            principal: Loan amount
            rate: Annual interest rate as a percentage
            years: Loan term in years
            
        Returns:
            Estimated monthly payment
        """
        monthly_rate = (rate / 100) / 12
        num_payments = years * 12
        
        # Handle edge case of zero interest
        if monthly_rate == 0:
            return principal / num_payments
        
        # Standard loan payment formula
        monthly_payment = principal * (monthly_rate * (1 + monthly_rate) ** num_payments) / ((1 + monthly_rate) ** num_payments - 1)
        return round(monthly_payment, 2)