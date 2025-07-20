# credit_system/tasks.py

import pandas as pd
from celery import shared_task
from decimal import Decimal, InvalidOperation
from datetime import datetime
import os
import logging
import traceback 
from django.db import transaction 
from .models import Customer, Loan
from .utils import calculate_emi 

logger = logging.getLogger(__name__)

@shared_task
@transaction.atomic
def ingest_data_from_excel_task(customer_file_name, loan_file_name):
    logger.info(f"Starting data ingestion for {customer_file_name} and {loan_file_name}...")
    
    base_data_path = '/app/data'
    customer_file_path = os.path.join(base_data_path, customer_file_name)
    loan_file_path = os.path.join(base_data_path, loan_file_name)

    # Ingest Customer Data
    try:
        customer_df = pd.read_excel(customer_file_path)
        customer_count = 0
        
        
        for index, row in customer_df.iterrows():
            row_num = index + 2 
            customer_data_processed = {} 
            
            try:
                customer_data_processed['customer_id'] = int(row['customer_id'])
                customer_data_processed['first_name'] = str(row['first_name'])
                customer_data_processed['last_name'] = str(row['last_name'])
                customer_data_processed['age'] = int(row['age'])

                phone_number_raw = row.get('phone_number')
                if pd.notna(phone_number_raw):
                  
                    if isinstance(phone_number_raw, (float, int)):
                        customer_data_processed['phone_number'] = str(int(phone_number_raw))
                    else:
                        customer_data_processed['phone_number'] = str(phone_number_raw)
                else:
                    customer_data_processed['phone_number'] = '' # Default empty string if NaN
                
              
                monthly_salary_raw = row['monthly_salary']
                approved_limit_raw = row['approved_limit']
              
                monthly_salary_decimal = Decimal(str(monthly_salary_raw)) if pd.notna(monthly_salary_raw) else Decimal('0.00')
                approved_limit_decimal = Decimal(str(approved_limit_raw)) if pd.notna(approved_limit_raw) else Decimal('0.00')

                
                current_debt_raw = row.get('current_debt') 
                current_debt_decimal = Decimal(str(current_debt_raw)) if pd.notna(current_debt_raw) else Decimal('0.00')
              

                Customer.objects.update_or_create(
                    customer_id=customer_data_processed['customer_id'],
                    defaults={
                        'first_name': customer_data_processed['first_name'],
                        'last_name': customer_data_processed['last_name'],
                        'age': customer_data_processed['age'],
                        'phone_number': customer_data_processed['phone_number'],
                        'monthly_salary': monthly_salary_decimal, # Use processed decimal
                        'approved_limit': approved_limit_decimal, # Use processed decimal
                        'current_debt': current_debt_decimal # Use processed decimal
                    }
                )
                customer_count += 1
            except KeyError as ke:
                logger.error(f"Customer data ingestion: Missing/mismatched column in row {row_num} of {customer_file_name}. Error: {ke}. Please check Excel headers. Full row data: {row.to_dict()}")
            except (ValueError, TypeError, InvalidOperation) as ve:
                logger.error(f"Customer data ingestion: Data type conversion error in row {row_num} of {customer_file_name}. Error: {ve}. Full row data: {row.to_dict()}")
            except Exception as e:
                logger.error(f"Customer data ingestion: Unexpected error in row {row_num} of {customer_file_name}: {e}\n{traceback.format_exc()}")
                
        logger.info(f"Customer data ingestion completed successfully. Ingested/Updated {customer_count} records.")
    except FileNotFoundError:
        logger.error(f"Error: Customer data file not found at {customer_file_path}. Please check file path and volume mount.")
    except Exception as e:
        logger.error(f"Error ingesting customer data from {customer_file_path}: {e}\n{traceback.format_exc()}")


    # Ingest Loan Data
    try:
        loan_df = pd.read_excel(loan_file_path)
        loan_count = 0
        for index, row in loan_df.iterrows():
            row_num = index + 2 
            loan_data_processed = {}
            try:
                customer_id_loan = int(row['customer id']) 
                loan_id = int(row['loan id']) 
                
                customer = Customer.objects.get(customer_id=customer_id_loan)
                
                # Loan Amount, Tenure, Interest Rate, Monthly Repayment, EMIs Paid on Time
                loan_amount_raw = row['loan amount']
                tenure_raw = row['tenure']
                interest_rate_raw = row['interest rate']
                monthly_repayment_raw = row['monthly repayment']
                emis_paid_on_time_raw = row['EMIs paid on time']

                loan_data_processed['loan_amount'] = Decimal(str(loan_amount_raw)) if pd.notna(loan_amount_raw) else Decimal('0.00')
                loan_data_processed['tenure'] = int(tenure_raw) if pd.notna(tenure_raw) else 0
                loan_data_processed['interest_rate'] = Decimal(str(interest_rate_raw)) if pd.notna(interest_rate_raw) else Decimal('0.00')
                loan_data_processed['monthly_repayment'] = Decimal(str(monthly_repayment_raw)) if pd.notna(monthly_repayment_raw) else Decimal('0.00')
                loan_data_processed['emis_paid_on_time'] = int(emis_paid_on_time_raw) if pd.notna(emis_paid_on_time_raw) else 0
                
                # Convert dates safely. pd.to_datetime with errors='coerce' turns unparseable dates into NaT
                start_date_raw = row['start date']
                end_date_raw = row['end date']
                
                loan_data_processed['start_date'] = pd.to_datetime(start_date_raw, errors='coerce').date() if pd.notna(start_date_raw) else None
                loan_data_processed['end_date'] = pd.to_datetime(end_date_raw, errors='coerce').date() if pd.notna(end_date_raw) else None

                Loan.objects.update_or_create(
                    loan_id=loan_id,
                    defaults={
                        'customer': customer,
                        'loan_amount': loan_data_processed['loan_amount'],
                        'tenure': loan_data_processed['tenure'],
                        'interest_rate': loan_data_processed['interest_rate'],
                        'monthly_repayment': loan_data_processed['monthly_repayment'],
                        'emis_paid_on_time': loan_data_processed['emis_paid_on_time'],
                        'start_date': loan_data_processed['start_date'],
                        'end_date': loan_data_processed['end_date'],
                        'status': 'APPROVED' # Assuming past loans are approved
                    }
                )
                loan_count += 1
            except Customer.DoesNotExist:
                logger.error(f"Loan data ingestion: Customer with ID {row.get('customer id', 'N/A')} not found for loan {row.get('loan id', 'N/A')}. Skipping loan in row {row_num}. Row data: {row.to_dict()}")
            except KeyError as ke:
                logger.error(f"Loan data ingestion: Missing/mismatched column in row {row_num} of {loan_file_name}. Error: {ke}. Please check Excel headers. Full row data: {row.to_dict()}")
            except (ValueError, TypeError, InvalidOperation) as ve:
                logger.error(f"Loan data ingestion: Data type conversion error in row {row_num} of {loan_file_name}. Error: {ve}. Full row data: {row.to_dict()}")
            except Exception as e:
                logger.error(f"Loan data ingestion: Unexpected error in row {row_num} of {loan_file_name}: {e}\n{traceback.format_exc()}")
                
        logger.info(f"Loan data ingestion completed successfully. Ingested/Updated {loan_count} records.")
    except FileNotFoundError:
        logger.error(f"Error: Loan data file not found at {loan_file_path}. Please check file path and volume mount.")
    except Exception as e:
        logger.error(f"Error ingesting loan data from {loan_file_path}: {e}\n{traceback.format_exc()}")