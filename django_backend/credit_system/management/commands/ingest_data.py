from django.core.management.base import BaseCommand
from django.db import transaction
from credit_system.models import Customer, Loan
import pandas as pd
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Ingest customer and loan data from Excel files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--customer_file',
            type=str,
            default='/app/customer_data.xlsx',
            help='Path to customer data Excel file'
        )
        parser.add_argument(
            '--loan_file',
            type=str,
            default='/app/loan_data.xlsx',
            help='Path to loan data Excel file'
        )

    def handle(self, *args, **options):
        customer_file = options['customer_file']
        loan_file = options['loan_file']
        
        try:
            # Check if files exist
            if not os.path.exists(customer_file):
                self.stdout.write(
                    self.style.ERROR(f'Customer file not found: {customer_file}')
                )
                return
            
            if not os.path.exists(loan_file):
                self.stdout.write(
                    self.style.ERROR(f'Loan file not found: {loan_file}')
                )
                return
            
            # Ingest customer data
            self.ingest_customer_data(customer_file)
            
            # Ingest loan data
            self.ingest_loan_data(loan_file)
            
            self.stdout.write(
                self.style.SUCCESS('Data ingestion completed successfully')
            )
            
        except Exception as e:
            logger.error(f"Error during data ingestion: {e}")
            self.stdout.write(
                self.style.ERROR(f'Error during data ingestion: {e}')
            )

    def ingest_customer_data(self, file_path):
        """Ingest customer data from Excel file"""
        try:
            # Read customer data
            df = pd.read_excel(file_path)
            
            self.stdout.write(f'Processing {len(df)} customers...')
            
            customers_created = 0
            customers_updated = 0
            
            with transaction.atomic():
                for _, row in df.iterrows():
                    # Create customer without specifying customer_id (let UUID auto-generate)
                    customer_data = {
                        'first_name': row['First Name'],
                        'last_name': row['Last Name'],
                        'age': int(row['Age']),
                        'phone_number': str(row['Phone Number']),
                        'monthly_income': int(row['Monthly Salary']),
                        'approved_limit': int(row['Approved Limit']),
                        'current_debt': 0
                    }
                    
                    # Check if customer exists by phone number
                    customer, created = Customer.objects.get_or_create(
                        phone_number=str(row['Phone Number']),
                        defaults=customer_data
                    )
                    
                    if created:
                        customers_created += 1
                    else:
                        # Update existing customer
                        customer.first_name = row['First Name']
                        customer.last_name = row['Last Name']
                        customer.age = int(row['Age'])
                        customer.monthly_income = int(row['Monthly Salary'])
                        customer.approved_limit = int(row['Approved Limit'])
                        customer.save()
                        customers_updated += 1
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Customer data ingested: {customers_created} created, {customers_updated} updated'
                )
            )
            
        except Exception as e:
            logger.error(f"Error ingesting customer data: {e}")
            raise

    def ingest_loan_data(self, file_path):
        """Ingest loan data from Excel file"""
        try:
            # Read loan data
            df = pd.read_excel(file_path)
            
            self.stdout.write(f'Processing {len(df)} loans...')
            
            loans_created = 0
            loans_updated = 0
            
            with transaction.atomic():
                for _, row in df.iterrows():
                    customer_id = str(row['Customer ID'])
                    
                    try:
                        # Find customer by original customer ID in phone number or create mapping
                        # For now, we'll skip loans that don't have matching customers
                        customer = Customer.objects.filter(
                            phone_number=str(row['Customer ID'])
                        ).first()
                        
                        if not customer:
                            # Try to find customer by index (this is a workaround)
                            try:
                                customer_index = int(row['Customer ID']) - 1
                                customer = Customer.objects.all()[customer_index]
                            except (ValueError, IndexError):
                                self.stdout.write(
                                    self.style.WARNING(
                                        f'Customer not found for loan {row["Loan ID"]} (Customer ID: {customer_id})'
                                    )
                                )
                                continue
                        
                        # Create loan without specifying loan_id (let UUID auto-generate)
                        loan_data = {
                            'customer': customer,
                            'loan_amount': float(row['Loan Amount']),
                            'tenure': int(row['Tenure']),
                            'interest_rate': float(row['Interest Rate']),
                            'monthly_installment': float(row['Monthly payment']),
                            'emis_paid_on_time': int(row['EMIs paid on Time']),
                            'start_date': pd.to_datetime(row['Date of Approval']),
                            'end_date': pd.to_datetime(row['End Date'])
                        }
                        
                        # Check if loan exists for this customer with same amount and start date
                        loan, created = Loan.objects.get_or_create(
                            customer=customer,
                            loan_amount=float(row['Loan Amount']),
                            start_date=pd.to_datetime(row['Date of Approval']),
                            defaults=loan_data
                        )
                        
                        if created:
                            loans_created += 1
                        else:
                            # Update existing loan
                            loan.tenure = int(row['Tenure'])
                            loan.interest_rate = float(row['Interest Rate'])
                            loan.monthly_installment = float(row['Monthly payment'])
                            loan.emis_paid_on_time = int(row['EMIs paid on Time'])
                            loan.end_date = pd.to_datetime(row['End Date'])
                            loan.save()
                            loans_updated += 1
                            
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(
                                f'Error processing loan {row["Loan ID"]}: {e}'
                            )
                        )
                        continue
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Loan data ingested: {loans_created} created, {loans_updated} updated'
                )
            )
            
        except Exception as e:
            logger.error(f"Error ingesting loan data: {e}")
            raise