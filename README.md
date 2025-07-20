# Credit Approval System (Backend)

A comprehensive credit approval system built with Python, Django, and Django Rest Framework, powered by PostgreSQL for data storage and Celery for background task processing. The system implements a detailed credit scoring algorithm and a full suite of loan management functionalities.

## 🚀 Features

### Core Functionality
- **Customer Registration**: Register new customers with automatic approved credit limit calculation.
- **Credit Scoring Algorithm**: Implements an advanced 5-component credit scoring system (0-100 scale) based on historical loan data.
- **Loan Eligibility Checking**: Provides real-time eligibility assessment for loan applications, including automatic adjustment of interest rates based on credit score.
- **Loan Creation**: Processes new loan requests, validating against calculated eligibility criteria before approval.
- **Loan Management**: Allows viewing detailed information for individual loans and retrieving full loan portfolios for specific customers.
- **Data Ingestion**: Automates the processing and ingestion of historical customer and loan data from Excel files into the database using background workers.

### Business Logic
- **Approved Credit Limit Calculation**: `approved_limit = 36 × monthly_salary` (rounded to nearest lakh).
- **Credit Score Components (0-100 scale)**:
    1.  **Payment History**: Based on EMIs paid on time versus total expected EMIs.
    2.  **Number of Loans Taken**: Quantity of past loans acquired by the customer.
    3.  **Current Year Activity**: Number of loans taken within the current calendar year.
    4.  **Loan Approved Volume**: Total sum of loan amounts previously approved for the customer, relative to their approved limit.
    5.  **Current Debt Check**: If the sum of current outstanding principal amount for a customer exceeds their approved limit, their credit score is immediately set to 0.

### Approval Criteria (from Credit Score and Financial Health)
- **Credit Score > 50**: Loan approved at the requested interest rate.
- **30 < Credit Score ≤ 50**: Loan approved, but with a minimum interest rate of 12%.
- **10 < Credit Score ≤ 30**: Loan approved, but with a minimum interest rate of 16%.
- **Credit Score ≤ 10**: Loan application is rejected.
- **Current EMIs vs. Salary**: If the sum of all current (active) monthly loan installments (EMIs), *plus* the potential EMI for the new loan, exceeds 50% of the customer's monthly salary, the loan is rejected.
- **Exceeding Approved Limit**: If the requested loan amount would push the customer's total outstanding debt beyond their `approved_limit`, the loan is rejected.

## 🛠️ Technology Stack

### Backend
- **Python 3.11+**
- **Django 4+**
- **Django Rest Framework (DRF)**: For building RESTful APIs.
- **PostgreSQL**: The primary relational database for data storage.
- **Celery**: For asynchronous background task processing (e.g., data ingestion).
- **Redis**: Serves as the message broker and results backend for Celery.
- **Pandas**: Utilized for efficient data processing and reading Excel files.
- **Openpyxl**: Python library for reading/writing Excel files, used by Pandas.
- **Psycopg2-binary**: PostgreSQL adapter for Python.
- **Gunicorn**: WSGI HTTP server used to run the Django application.
- **Dj-database-url**: Simplifies database URL configuration for Django.
- **Python-dotenv**: For loading environment variables in local development.
- **Django-cors-headers**: Handles Cross-Origin Resource Sharing (CORS) for API access.

### Containerization
- **Docker**
- **Docker Compose**: For defining and running the multi-container application (Django app, PostgreSQL, Redis, Celery worker).

## 📁 Project Structure

```

credit-system-main/ \# Your project root
├── docker-compose.yml    \# Defines Docker services (Django, DB, Redis, Worker)
├── README.md             \# This file
├── .dockerignore         \# Specifies files/folders to ignore during Docker build
├── django\_backend/       \# Django project root (build context for Docker)
│   ├── .env              \# Environment variables (e.g., SECRET\_KEY, DEBUG)
│   ├── Dockerfile        \# Defines the Docker image for Django/Celery services
│   ├── manage.py         \# Django's command-line utility
│   ├── requirements.txt  \# Python dependencies
│   ├── credit\_approval\_system/ \# Your main Django project module
│   │   ├── **init**.py   \# Initializes Celery app
│   │   ├── settings.py   \# Django project settings
│   │   ├── urls.py       \# Main URL routing
│   │   ├── wsgi.py       \# WSGI entry point
│   │   └── celery.py     \# Celery application setup
│   ├── credit\_system/    \# Your main Django application (Django app)
│   │   ├── **init**.py
│   │   ├── admin.py      \# Django Admin configuration
│   │   ├── apps.py
│   │   ├── migrations/   \# Database migration files
│   │   ├── models.py     \# Database models (Customer, Loan, CreditScore)
│   │   ├── serializers.py\# Data serialization/deserialization
│   │   ├── urls.py       \# App-specific URL routing
│   │   ├── views.py      \# API view logic (endpoints)
│   │   ├── tasks.py      \# Celery tasks (e.g., data ingestion)
│   │   └── utils.py      \# Utility functions (e.g., credit score calculation)
│   └── data/             \# Contains Excel data files
│       ├── customer\_data.xlsx
│       └── loan\_data.xlsx

````

## 🚀 Quick Start

### Prerequisites
- **Docker Desktop** installed and running (for Windows/macOS, includes Docker Compose).
- **Git** (for cloning the repository).

### Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd credit-approval-system # Or the name of your cloned folder
    ```

2.  **Place Data Files:**
    Ensure `customer_data.xlsx` and `loan_data.xlsx` are placed in the `credit-system-main/data/` directory.

3.  **Build and Start Docker Containers (Comprehensive Setup):**
    This command will build the necessary Docker images, set up the network, create volumes, run database migrations, and start all services (PostgreSQL, Redis, Django Web App, Celery Worker).
    ```bash
    docker compose up --build -d
    ```
    * **Troubleshooting during this step:** If you encounter issues (e.g., "resource still in use", "cannot cast type", "no such file or directory for data"), refer to common Docker troubleshooting steps like:
        * `docker compose down --volumes --rmi all`
        * `docker system prune --all --force --volumes`
        * **Restart Docker Desktop / Reboot PC**
        * Ensure `models.py` changes are reflected in migrations (delete `00xx_*.py` files in `migrations/` and re-run `docker compose run web python manage.py makemigrations` before `up --build -d`).

4.  **Verify All Containers are Running:**
    ```bash
    docker ps
    ```
    You should see `credit-system-main-web-1`, `credit-system-main-worker-1`, `credit-system-main-db-1`, and `credit-system-main-redis-1` listed with `STATUS` showing `Up ...`.

### Accessing the Application & API

- **Backend API Base URL:** `http://localhost:8000/api/`
- **API Testing Tool:** Use **Thunder Client (VS Code Extension)** or **Postman** to send requests.

## 📊 API Endpoints (Testing Order Recommended)

**Important Notes for all API calls:**
- All `POST` request URLs should end with a **trailing slash `/`**.
- For all `POST` requests, ensure you set the **`Content-Type: application/json`** header.
- For `GET` requests, no request body or `Content-Type` header is needed.

### 1. Ingest Initial Data (REQUIRED to populate DB)

* **Method:** `POST`
* **URL:** `http://localhost:8000/api/ingest-data/`
* **Purpose:** Triggers the background task to load historical customer and loan data from Excel files into the database.
* **Request Body (JSON):**
    ```json
    {
        "customer_file": "customer_data.xlsx",
        "loan_file": "loan_data.xlsx"
    }
    ```
* **Expected Response (202 Accepted):**
    ```json
    {
        "message": "Data ingestion started in the background. Check worker logs for progress."
    }
    ```
    * **Verification:** Check `docker compose logs web --tail 500` for "Customer data ingested successfully. Ingested/Updated X records." and "Loan data ingested successfully. Ingested/Updated Y records." messages. (These confirm your database is populated).

### 2. Register Customer

* **Method:** `POST`
* **URL:** `http://localhost:8000/api/register/`
* **Purpose:** Registers a new customer and calculates their approved credit limit.
* **Request Body (JSON):**
    ```json
    {
        "first_name": "New",
        "last_name": "User",
        "age": 25,
        "monthly_income": 45000,
        "phone_number": "1112223330" 
    }
    ```
* **Expected Response (201 Created):**
    ```json
    {
        "customer_id": 301, // Or next available integer ID after your 300 ingested
        "first_name": "New", "last_name": "User", "age": 25, "phone_number": "1112223330",
        "monthly_salary": 45000, "approved_limit": "1620000.00", "current_debt": "0.00"
    }
    ```
    * **Note:** Change `phone_number` for each new registration, as it must be unique. If you get `Key (customer_id)=(X) already exists`, run `docker compose run web python manage.py dbshell` and then `SELECT setval('credit_system_customer_customer_id_seq', (SELECT MAX(customer_id) FROM credit_system_customer));` then `\q` to fix sequence, then retry `register`.

### 3. Check Eligibility

* **Method:** `POST`
* **URL:** `http://localhost:8000/api/check-eligibility/`
* **Purpose:** Calculates credit score and determines loan approval status, suggesting a corrected interest rate.
* **Request Body (JSON):**
    ```json
    {
        "customer_id": 1,          // Use an ID from ingested data (1-300) or one you registered
        "loan_amount": 500000.00,  
        "interest_rate": 8.00,     
        "tenure": 48               
    }
    ```
* **Expected Response (200 OK):**
    ```json
    {
        "customer_id": 1,
        "approval": true,             // true or false
        "interest_rate": 8.00,
        "corrected_interest_rate": 8.00, // Could be 12.00, 16.00, or 100.00 (if score too low)
        "tenure": 48,
        "monthly_installment": "12108.00" 
    }
    ```
    * **Note:** Test various scenarios (good credit, mid-tier, low-tier, very low credit, high EMIs, exceeding approved limit) to verify your logic.

### 4. Create Loan

* **Method:** `POST`
* **URL:** `http://localhost:8000/api/create-loan/`
* **Purpose:** Processes and creates a new loan if eligibility criteria are met.
* **Request Body (JSON):**
    ```json
    {
        "customer_id": 1,          // Use an existing customer ID
        "loan_amount": 100000.00,  
        "interest_rate": 9.00,     
        "tenure": 12               
    }
    ```
* **Expected Response (201 Created for approval, 200 OK for rejection):**
    * **Approved:**
        ```json
        {
            "loan_id": 1001, // Next available integer loan ID (e.g., after 782 ingested)
            "customer_id": 1,
            "loan_approved": true,
            "message": "Loan approved successfully",
            "monthly_installment": "8745.00"
        }
        ```
    * **Rejected:**
        ```json
        {
            "loan_id": null,
            "customer_id": 1,
            "loan_approved": false,
            "message": "Loan rejected: Credit score too low", 
            "monthly_installment": "0.00"
        }
        ```

### 5. View Loan Details

* **Method:** `GET`
* **URL Example:** `http://localhost:8000/api/view-loan/101/`
* **Purpose:** Retrieves details for a specific loan and its associated customer.
* **Request Body:** None
* **Note:** Replace `101` in the URL with an actual `loan_id` from your ingested `loan_data.xlsx` or a loan you just created.

* **Expected Response (200 OK):**
    ```json
    {
        "loan_id": 101, 
        "customer": { 
            "customer_id": 1, "first_name": "Aaron", "last_name": "Garcia",
            "phone_number": "9629317944", "age": 63
        },
        "loan_amount": "500000.00", "interest_rate": "8.00",
        "monthly_repayment": "12108.00", "tenure": 48
    }
    ```

### 6. View Customer's All Loans

* **Method:** `GET`
* **URL Example:** `http://localhost:8000/api/view-loans/1/`
* **Purpose:** Retrieves a list of all active loans for a specific customer.
* **Request Body:** None
* **Note:** Replace `1` in the URL with an actual `customer_id` from your ingested `customer_data.xlsx`.

* **Expected Response (200 OK):** A JSON array (list) of loan objects:
    ```json
    [
        {
            "loan_id": 1001,
            "loan_amount": "100000.00", "interest_rate": "9.00",
            "monthly_repayment": "8745.00",
            "repayments_left": 12 
        },
        // ... more loan objects for this customer ...
    ]
    ```
````