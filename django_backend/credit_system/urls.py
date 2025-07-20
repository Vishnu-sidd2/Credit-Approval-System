from django.urls import path
from .views import IngestDataView 
from . import views

urlpatterns = [


    path('', views.health_check, name='health_check'),
    path('register/', views.register_customer, name='register_customer'),
    path('check-eligibility/', views.check_loan_eligibility, name='check_loan_eligibility'),
    path('create-loan/', views.create_loan, name='create_loan'),
    path('view-loan/<int:loan_id>/', views.view_loan, name='view_loan'),
    path('view-loans/<int:customer_id>/', views.view_customer_loans, name='view_customer_loans'),
    path('ingest-data/', IngestDataView.as_view(), name='ingest_data'),
    
]