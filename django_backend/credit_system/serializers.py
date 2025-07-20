from rest_framework import serializers
from .models import Customer, Loan 


class CustomerSerializer(serializers.ModelSerializer):
    """Customer serializer for API responses"""

    class Meta:
        model = Customer
        fields = ['customer_id', 'first_name', 'last_name', 'age', 'phone_number', 
                  'monthly_salary', 'approved_limit', 'current_debt']
        read_only_fields = ['customer_id', 'approved_limit', 'current_debt']


class CustomerRegistrationSerializer(serializers.ModelSerializer):
    """Customer registration serializer (now a ModelSerializer)"""

    class Meta:
        model = Customer
        fields = ['first_name', 'last_name', 'age', 'phone_number', 'monthly_salary']

    # Remove custom create method if approved_limit is calculated in Customer model's save()
    # def create(self, validated_data):
    #    customer = Customer(**validated_data)
    #    customer.save() # approved_limit calculation now in model's save()
    #    return customer


class LoanSerializer(serializers.ModelSerializer):
    """Loan serializer for API responses"""

    customer_id = serializers.IntegerField(source='customer.customer_id', read_only=True)
    # repayments_left is a property on the Loan model
    repayments_left = serializers.ReadOnlyField() 

    class Meta:
        model = Loan
        # Corrected: Use 'monthly_repayment' and 'status' as per updated model
        fields = ['loan_id', 'customer_id', 'loan_amount', 'tenure', 'interest_rate',
                  'monthly_repayment', 'emis_paid_on_time', 'start_date', 'end_date',
                  'repayments_left', 'status'] # Added status, ensuring monthly_repayment
        # Corrected: Added 'repayments_left' and 'status' to read_only_fields if not directly settable by API
        read_only_fields = ['loan_id', 'monthly_repayment', 'end_date', 'repayments_left', 'status'] 


class LoanEligibilitySerializer(serializers.Serializer):
    """Loan eligibility check serializer (for request body)"""

    customer_id = serializers.IntegerField()
    loan_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    tenure = serializers.IntegerField()


class LoanEligibilityResponseSerializer(serializers.Serializer):
    """Loan eligibility response serializer (for response body)"""

    customer_id = serializers.IntegerField()
    approval = serializers.BooleanField()
    interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    corrected_interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    tenure = serializers.IntegerField()
    monthly_installment = serializers.DecimalField(max_digits=12, decimal_places=2) # Corrected to DecimalField


class LoanCreationSerializer(serializers.Serializer):
    """Loan creation serializer (for request body)"""

    customer_id = serializers.IntegerField()
    loan_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    tenure = serializers.IntegerField()


class LoanCreationResponseSerializer(serializers.Serializer):
    """Loan creation response serializer (for response body)"""

    loan_id = serializers.IntegerField(allow_null=True)
    customer_id = serializers.IntegerField()
    loan_approved = serializers.BooleanField()
    message = serializers.CharField()
    monthly_installment = serializers.DecimalField(max_digits=15, decimal_places=2)


class LoanDetailSerializer(serializers.ModelSerializer):
    """Detailed loan serializer with customer info"""

    customer = CustomerSerializer(read_only=True) 

    class Meta:
        model = Loan
        
        fields = ['loan_id', 'customer', 'loan_amount', 'interest_rate', 
                  'monthly_repayment', 'tenure', 'status'] 

   


class CustomerLoanSerializer(serializers.ModelSerializer):
    """Customer loan list serializer"""

    repayments_left = serializers.ReadOnlyField() 

    class Meta:
        model = Loan
        
        fields = ['loan_id', 'loan_amount', 'interest_rate', 'monthly_repayment', 
                  'repayments_left', 'status'] # Added status