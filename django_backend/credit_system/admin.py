# credit_system/admin.py
from django.contrib import admin
from .models import Customer, Loan, CreditScore


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        'customer_id', 
        'first_name', 
        'last_name', 
        'phone_number', 
        'age', 
        'monthly_salary', 
        'approved_limit', 
        'current_debt',
        'created_at', 
        'updated_at'  
    )
    ordering = ('-created_at',) 
    list_filter = ('age', 'created_at') 
    search_fields = ('first_name', 'last_name', 'phone_number', 'customer_id')
    readonly_fields = ('customer_id', 'approved_limit', 'current_debt', 'created_at', 'updated_at') 

    fieldsets = (
        ('Personal Information', {
            'fields': ('customer_id', 'first_name', 'last_name', 'age', 'phone_number')
        }),
        ('Financial Information', {
            'fields': ('monthly_salary', 'approved_limit', 'current_debt')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = (
        'loan_id', 
        'customer', 
        'loan_amount', 
        'tenure', 
        'interest_rate', 
        'monthly_repayment',
        'emis_paid_on_time', 
        'start_date', 
        'end_date', 
        'status', 
        'created_at', 
        'updated_at'  
    )
    ordering = ('-created_at',) 
    list_filter = ('status', 'interest_rate', 'tenure', 'created_at') 
    search_fields = ('loan_id', 'customer__first_name', 'customer__last_name')
    readonly_fields = ('loan_id', 'monthly_repayment', 'created_at', 'updated_at') 

    fieldsets = (
        ('Loan Information', {
            'fields': ('loan_id', 'customer', 'loan_amount', 'tenure', 'interest_rate')
        }),
        ('Payment Information', {
            'fields': ('monthly_repayment', 'emis_paid_on_time')
        }),
        ('Dates', {
            'fields': ('start_date', 'end_date')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(CreditScore)
class CreditScoreAdmin(admin.ModelAdmin):
    list_display = (
        'customer', 
        'score', 
        'calculated_at' 
       
    )
    search_fields = ('customer__customer_id',)
    list_filter = ('score', 'calculated_at')
    readonly_fields = ('calculated_at',) # Corrected list
    ordering = ('-calculated_at',) 

    fieldsets = (
        ('Credit Score', {
            'fields': ('customer', 'score', 'calculated_at')
        }),
       
    )