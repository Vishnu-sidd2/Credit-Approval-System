# credit_system/utils.py

from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
import logging
import math
from django.db.models import Sum # Added for aggregation
from django.utils import timezone

logger = logging.getLogger(__name__)


def calculate_emi(principal, annual_interest_rate, tenure_months):
    principal = Decimal(principal)
    annual_interest_rate = Decimal(annual_interest_rate)
    tenure_months = int(tenure_months)

    if annual_interest_rate == 0: 
        return principal / tenure_months

    monthly_interest_rate = annual_interest_rate / Decimal('100') / Decimal('12') 

    if monthly_interest_rate == 0:
        return (principal / tenure_months).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    numerator = principal * monthly_interest_rate * (Decimal('1') + monthly_interest_rate)**tenure_months
    denominator = ((Decimal('1') + monthly_interest_rate)**tenure_months - Decimal('1'))

    return (numerator / denominator).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) # Ensure final result is quantized

class CreditScoreCalculator:
    """Calculates credit score and loan eligibility/corrections."""

    def calculate_credit_score(self, customer):
        """
        Calculates credit score (out of 100) based on historical loan data.
        Considers: Past Loans paid on time, No of loans taken, Loan activity in current year, Loan approved volume.
        If sum of current loans (outstanding principal) > approved limit, score is 0.
        """
        try:
            loans = customer.loans.all()
            
            if customer.current_debt > customer.approved_limit:
                logger.info(f"Customer {customer.customer_id}: Current outstanding debt {customer.current_debt} > Approved limit {customer.approved_limit}. Credit score = 0.")
                return 0 
            
            if not loans.exists():
                return 100

            credit_score = Decimal('100') 

            total_expected_emis = Decimal('0')
            total_emis_paid_on_time = Decimal('0')

            for loan in loans:
                total_emis_paid_on_time += loan.emis_paid_on_time
                if loan.status == 'APPROVED' and loan.end_date > timezone.now().date():
                    months_passed_since_start = (timezone.now().date().year - loan.start_date.year) * 12 + \
                                                (timezone.now().date().month - loan.start_date.month)
                    total_expected_emis += min(loan.tenure, months_passed_since_start) 
                else:
                    total_expected_emis += loan.tenure 

            if total_expected_emis > 0:
                on_time_ratio = total_emis_paid_on_time / total_expected_emis
                if on_time_ratio < Decimal('0.9'): 
                    credit_score -= (Decimal('1') - on_time_ratio) * Decimal('30') 
            else:
                on_time_ratio = Decimal('1')

            num_loans = loans.count()
            if num_loans > 5:
                credit_score -= (num_loans - 5) * Decimal('3')

            current_year = timezone.now().year
            current_year_loans_count = loans.filter(start_date__year=current_year).count()
            if current_year_loans_count > 2:
                credit_score -= (current_year_loans_count - 2) * Decimal('5') 

            total_approved_volume = loans.aggregate(Sum('loan_amount'))['loan_amount__sum'] or Decimal('0.00')
            if customer.approved_limit > 0:
                utilization_ratio = total_approved_volume / customer.approved_limit
                if utilization_ratio > Decimal('0.8'): # If > 80% of limit ever approved
                    credit_score -= (utilization_ratio - Decimal('0.8')) * Decimal('20') # Deduct more for higher utilization

            # Ensure score is within 0-100 range
            return max(0, min(100, int(credit_score)))

        except Exception as e:
            logger.error(f"Error calculating credit score for customer {customer.customer_id}: {e}", exc_info=True)
            return 0 # Return 0 on any calculation error


    def determine_corrected_interest_rate(self, credit_score, requested_rate):
        """Determines the corrected interest rate based on credit score slabs."""
        requested_rate = Decimal(requested_rate)

        if credit_score > 50:
            return requested_rate  # No correction needed, lowest interest is fine
        elif 30 < credit_score <= 50:
            # If requested rate is lower than 12%, correct it to 12%. Otherwise, use requested.
            return max(Decimal('12.00'), requested_rate).quantize(Decimal('0.01'))
        elif 10 < credit_score <= 30:
            # If requested rate is lower than 16%, correct it to 16%. Otherwise, use requested.
            return max(Decimal('16.00'), requested_rate).quantize(Decimal('0.01'))
        else: # credit_score <= 10
            # Loan will be rejected, but return a high rate as a "corrected" rate
            return Decimal('100.00') # Effectively disallow loan with high rate, or return 0, depending on desired response.


    def check_loan_approval(self, customer, loan_amount, requested_interest_rate, tenure):
        """
        Checks if a loan should be approved based on credit score, current EMIs, and approved limit.
        Returns approval status (bool), message (str), corrected_interest_rate (Decimal), monthly_installment (Decimal).
        """
        try:
            loan_amount = Decimal(loan_amount)
            requested_interest_rate = Decimal(requested_interest_rate)
            tenure = int(tenure)

            credit_score = self.calculate_credit_score(customer)
            
            # Determine the potentially corrected interest rate based on score
            corrected_interest_rate = self.determine_corrected_interest_rate(credit_score, requested_interest_rate)
            
            # Calculate potential EMI with the corrected rate
            potential_monthly_installment = calculate_emi(loan_amount, corrected_interest_rate, tenure)

            # --- Assignment Rule: If sum of all current EMIs > 50% of monthly salary, don’t approve any loans ---
            current_active_loans = customer.loans.filter(status='APPROVED', end_date__gt=timezone.now().date())
            sum_current_emis = current_active_loans.aggregate(Sum('monthly_repayment'))['monthly_repayment__sum'] or Decimal('0.00')
            
            # Check if sum of current EMIs *plus new loan's potential EMI* exceeds 50% of monthly salary
            if (sum_current_emis + potential_monthly_installment) > (Decimal('0.50') * customer.monthly_salary):
                message = "Sum of current EMIs (including potential new loan) exceeds 50% of monthly salary."
                logger.info(f"Customer {customer.customer_id}: {message}")
                return False, message, corrected_interest_rate, potential_monthly_installment

            # --- Assignment Rule: If credit_rating <= 10, don't approve any loans ---
            if credit_score <= 10:
                message = "Credit score is too low."
                logger.info(f"Customer {customer.customer_id}: {message} (Score: {credit_score})")
                return False, message, corrected_interest_rate, potential_monthly_installment

            # --- Check if new loan amount would exceed remaining approved limit ---
            # customer.current_debt holds the sum of outstanding principal from model (updated on loan creation/payment)
            remaining_approved_limit = customer.approved_limit - customer.current_debt
            if loan_amount > remaining_approved_limit:
                message = f"Requested loan amount {loan_amount} exceeds remaining approved limit {remaining_approved_limit}."
                logger.info(f"Customer {customer.customer_id}: {message}")
                return False, message, corrected_interest_rate, potential_monthly_installment
            
            # --- If all checks pass, loan is approved ---
            approval_message = "Loan approved."
            return True, approval_message, corrected_interest_rate, potential_monthly_installment

        except Exception as e:
            logger.error(f"Error in loan approval check for customer {customer.customer_id}: {e}", exc_info=True)
            return False, "Internal error during eligibility check.", requested_interest_rate, Decimal('0.00')