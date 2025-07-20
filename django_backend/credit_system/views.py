# credit_system/views.py
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView 
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal 

from .tasks import ingest_data_from_excel_task
import logging

from .models import Customer, Loan 
from .serializers import (
    CustomerSerializer, CustomerRegistrationSerializer, LoanSerializer,
    LoanEligibilitySerializer, LoanEligibilityResponseSerializer,
    LoanCreationSerializer, LoanCreationResponseSerializer,
    LoanDetailSerializer, CustomerLoanSerializer
)
from .utils import calculate_emi, CreditScoreCalculator 

logger = logging.getLogger(__name__)


@api_view(['GET'])
def health_check(request):
    """Health check endpoint"""
    return Response({
        'message': 'Credit Approval System API is running',
        'version': '1.0.0',
        'timestamp': timezone.now()
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
def register_customer(request):
    """Register a new customer"""
    try:
        serializer = CustomerRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            monthly_salary = serializer.validated_data['monthly_salary'] 

            customer = serializer.save(monthly_salary=monthly_salary) 

            response_serializer = CustomerSerializer(customer)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error registering customer: {str(e)}", exc_info=True)
        return Response(
            {'error': 'Internal server error during customer registration'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def check_loan_eligibility(request):
    """Check loan eligibility for a customer"""
    try:
        serializer = LoanEligibilitySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        customer_id = data['customer_id']
        loan_amount = Decimal(data['loan_amount']) 
        interest_rate = Decimal(data['interest_rate']) 
        tenure = data['tenure']

        customer = get_object_or_404(Customer, customer_id=customer_id)

        calculator = CreditScoreCalculator()
        
        approval_status, message, corrected_interest_rate, monthly_installment = \
            calculator.check_loan_approval(customer, loan_amount, interest_rate, tenure)

        response_data = {
            'customer_id': customer_id,
            'approval': approval_status,
            'interest_rate': interest_rate, 
            'corrected_interest_rate': corrected_interest_rate,
            'tenure': tenure,
            'monthly_installment': monthly_installment
        }

        response_serializer = LoanEligibilityResponseSerializer(data=response_data)
        if response_serializer.is_valid():
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        
        logger.error(f"LoanEligibilityResponseSerializer validation failed: {response_serializer.errors}")
        return Response(response_serializer.errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Customer.DoesNotExist:
        return Response({'error': 'Customer not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error checking loan eligibility: {str(e)}", exc_info=True)
        return Response(
            {'error': 'Internal server error during eligibility check'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def create_loan(request):
    """Process a new loan based on eligibility."""
    try:
        serializer = LoanCreationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        customer_id = data['customer_id']
        loan_amount = Decimal(data['loan_amount']) 
        interest_rate = Decimal(data['interest_rate']) 
        tenure = data['tenure']

        customer = get_object_or_404(Customer, customer_id=customer_id)

        calculator = CreditScoreCalculator()
        approval_status, message, final_interest_rate, monthly_installment = \
            calculator.check_loan_approval(customer, loan_amount, interest_rate, tenure)

        loan_id = None
        if approval_status:
            start_date = timezone.now().date()
            end_date = (start_date + timedelta(days=30 * tenure)).replace(day=1) - timedelta(days=1) 

            loan = Loan.objects.create(
                customer=customer,
                loan_amount=loan_amount,
                tenure=tenure,
                interest_rate=final_interest_rate,
                monthly_repayment=monthly_installment,
                start_date=start_date,
                end_date=end_date,
                emis_paid_on_time=0, 
                status='APPROVED'
            )
            loan_id = loan.loan_id

            customer.current_debt += loan_amount
            customer.save() 

            response_status = status.HTTP_201_CREATED
        else:
            response_status = status.HTTP_200_OK # Still 200 OK for a rejection message

        response_data = {
            'loan_id': loan_id,
            'customer_id': customer_id,
            'loan_approved': approval_status,
            'message': message,
            'monthly_installment': monthly_installment
        }

        response_serializer = LoanCreationResponseSerializer(data=response_data)
        if response_serializer.is_valid():
            return Response(response_serializer.data, status=response_status)
        
        logger.error(f"LoanCreationResponseSerializer validation failed: {response_serializer.errors}")
        return Response(response_serializer.errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Customer.DoesNotExist:
        return Response({'error': 'Customer not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error creating loan: {str(e)}", exc_info=True)
        return Response(
            {'error': 'Internal server error during loan creation'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def view_loan(request, loan_id):
    """View loan details by loan ID"""
    try:
        loan = get_object_or_404(Loan, loan_id=loan_id)
        serializer = LoanDetailSerializer(loan)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error viewing loan {loan_id}: {str(e)}", exc_info=True)
        return Response(
            {'error': 'Loan not found or internal server error'},
            status=status.HTTP_404_NOT_FOUND # Return 404 for not found, 500 for other errors
        )


@api_view(['GET'])
def view_customer_loans(request, customer_id):
    """View all current loan details by customer ID"""
    try:
        customer = get_object_or_404(Customer, customer_id=customer_id)
        # Filter for active loans (end_date in the future)
        current_loans = Loan.objects.filter(
            customer=customer,
            end_date__gt=timezone.now().date(),
            status='APPROVED' # Only consider approved loans
        ).order_by('-start_date') # Order by most recent first

        serializer = CustomerLoanSerializer(current_loans, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Customer.DoesNotExist:
        return Response({'error': 'Customer not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error viewing customer {customer_id} loans: {str(e)}", exc_info=True)
        return Response(
            {'error': 'Internal server error during viewing customer loans'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# This view is for triggering the background ingestion task
# It should be a class-based view if you want to use APIView
class IngestDataView(APIView):
    def post(self, request):
        try:
            # Get filenames from the request body
            customer_file_name = request.data.get('customer_file')
            loan_file_name = request.data.get('loan_file')

            if not customer_file_name or not loan_file_name:
                return Response(
                    {"error": "Both 'customer_file' and 'loan_file' must be provided in the request body."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Trigger the Celery task with the filenames
            # The task will handle the actual ingestion in the background
            ingest_data_from_excel_task.delay(customer_file_name, loan_file_name)
            
            return Response(
                {"message": "Data ingestion started in the background. Check worker logs for progress."},
                status=status.HTTP_202_ACCEPTED # 202 Accepted indicates processing has begun
            )
        except Exception as e:
            logger.error(f"Unexpected error during data ingestion request: {e}", exc_info=True)
            return Response(
                {"error": "Internal server error during ingestion request. Check web logs for details."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )