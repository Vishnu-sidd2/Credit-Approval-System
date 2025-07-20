# credit_system/models.py

from django.db import models
from decimal import Decimal, ROUND_HALF_UP 
from django.core.validators import MinValueValidator, MaxValueValidator 
import math
from django.utils import timezone # ADDED: For auto_now_add/auto_now

class Customer(models.Model):
    customer_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    age = models.IntegerField()
    phone_number = models.CharField(max_length=15, unique=True)
    monthly_salary = models.IntegerField(validators=[MinValueValidator(0)])
    approved_limit = models.DecimalField(max_digits=15, decimal_places=2) 
    current_debt = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    # ADDED: Common auditing fields
    created_at = models.DateTimeField(auto_now_add=True) 
    updated_at = models.DateTimeField(auto_now=True)     

    def save(self, *args, **kwargs):
        if not self.approved_limit or self.approved_limit == 0:
            calculated_limit = Decimal('36') * Decimal(str(self.monthly_salary)) 
            self.approved_limit = (calculated_limit / Decimal('100000')).quantize(Decimal('1.'), rounding=ROUND_HALF_UP) * Decimal('100000')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.customer_id})"

class Loan(models.Model):
    loan_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='loans')
    loan_amount = models.DecimalField(max_digits=10, decimal_places=2)
    tenure = models.IntegerField() 
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    monthly_repayment = models.DecimalField(max_digits=10, decimal_places=2) 
    emis_paid_on_time = models.IntegerField(default=0)
    start_date = models.DateField()
    end_date = models.DateField()

    LOAN_STATUS_CHOICES = [
        ('PENDING', 'Pending'), ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'), ('PAID', 'Paid'),
    ]
    status = models.CharField(max_length=10, choices=LOAN_STATUS_CHOICES, default='PENDING')

    # ADDED: Common auditing fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def repayments_left(self):
        return max(0, self.tenure - self.emis_paid_on_time)

    def __str__(self):
        return f"Loan {self.loan_id} for {self.customer.first_name}"


class CreditScore(models.Model): 
    customer = models.OneToOneField(
        'Customer', on_delete=models.CASCADE, primary_key=True, related_name='credit_score'
    )
    score = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)], 
        default=0
    )
    # ADDED: Calculated_at field
    calculated_at = models.DateTimeField(auto_now=True) 

    def __str__(self):
        return f"Credit Score for Customer {self.customer.customer_id}: {self.score}"