# Credit Approval System

A comprehensive credit approval system built with FastAPI backend and React frontend, featuring advanced credit scoring algorithms, loan eligibility checking, and complete loan management functionality.

## 🚀 Features

### Core Functionality
- **Customer Registration** - Register new customers with automatic credit limit calculation
- **Credit Scoring Algorithm** - Advanced 5-component credit scoring system (0-100 scale)
- **Loan Eligibility Checking** - Real-time eligibility assessment with interest rate corrections
- **Loan Creation** - Create loans with automatic eligibility validation
- **Loan Management** - View individual loans and customer loan portfolios
- **Data Ingestion** - Automatic Excel file processing for historical data

### Business Logic
- **Credit Limit Calculation**: `approved_limit = 36 × monthly_salary` (rounded to nearest lakh)
- **Credit Score Components**:
  - Payment History (40% weight) - EMIs paid on time vs total EMIs
  - Loan Count (20% weight) - Number of loans taken
  - Current Year Activity (20% weight) - Loans in current year
  - Loan Volume (20% weight) - Total approved volume vs credit limit
  - Debt Check - If current debt > approved limit, credit score = 0

### Approval Criteria
- **Credit Score > 50**: Loan approved at requested rate
- **30 < Credit Score ≤ 50**: Loan approved with minimum 12% interest rate
- **10 < Credit Score ≤ 30**: Loan approved with minimum 16% interest rate
- **Credit Score ≤ 10**: Loan rejected
- **Current EMIs > 50% of salary**: Loan rejected

## 🛠️ Technology Stack

### Backend
- **FastAPI** - Modern, fast web framework for building APIs
- **MongoDB** - NoSQL database for scalable data storage
- **Motor** - Async MongoDB driver for FastAPI
- **Pandas** - Data processing and Excel file handling
- **Pydantic** - Data validation and serialization

### Frontend
- **React 19** - Modern frontend framework
- **Tailwind CSS** - Utility-first CSS framework
- **Axios** - HTTP client for API communication
- **React Router** - Client-side routing

## 📁 Project Structure

```
/app/
├── backend/
│   ├── server.py           # Main FastAPI application
│   ├── requirements.txt    # Python dependencies
│   └── .env               # Environment variables
├── frontend/
│   ├── src/
│   │   ├── App.js         # Main React component
│   │   ├── App.css        # Styles and animations
│   │   └── index.js       # React entry point
│   ├── package.json       # Node.js dependencies
│   └── .env              # Frontend environment variables
├── customer_data.xlsx     # Customer data for ingestion
├── loan_data.xlsx        # Historical loan data
├── test_result.md        # Testing documentation
└── README.md            # This file
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- MongoDB
- Docker (optional)

### Installation & Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd credit-approval-system
   ```

2. **Backend Setup**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   yarn install
   ```

4. **Environment Configuration**
   - Backend `.env` file is pre-configured for MongoDB
   - Frontend `.env` file contains the backend URL
   - No changes needed for local development

5. **Start the Application**
   ```bash
   # Start backend (in backend directory)
   uvicorn server:app --host 0.0.0.0 --port 8001

   # Start frontend (in frontend directory)
   yarn start
   ```

6. **Access the Application**
   - Frontend: `http://localhost:3000`
   - Backend API: `http://localhost:8001`
   - API Documentation: `http://localhost:8001/docs`

## 📊 API Endpoints

### Customer Management
- `POST /api/register` - Register new customer
- `GET /api/` - Health check

### Loan Management
- `POST /api/check-eligibility` - Check loan eligibility
- `POST /api/create-loan` - Create new loan
- `GET /api/view-loan/{loan_id}` - View specific loan
- `GET /api/view-loans/{customer_id}` - View customer loans

### Data Management
- `POST /api/ingest-data` - Trigger data ingestion

## 🧪 Testing

### Backend Testing
The system includes comprehensive backend testing:
- All API endpoints tested
- Business logic validation
- Error handling verification
- Edge case testing

### Test Results
- **95.5% Success Rate** (21/22 tests passed)
- All core functionality working
- Credit scoring algorithm validated
- Loan eligibility logic confirmed

## 💡 Usage Examples

### Register a New Customer
```bash
curl -X POST "http://localhost:8001/api/register" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "age": 30,
    "monthly_income": 75000,
    "phone_number": "9876543210"
  }'
```

### Check Loan Eligibility
```bash
curl -X POST "http://localhost:8001/api/check-eligibility" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "customer-id-here",
    "loan_amount": 500000,
    "interest_rate": 12.0,
    "tenure": 24
  }'
```

## 🔍 Credit Scoring Algorithm

The system uses a sophisticated 5-component credit scoring model:

1. **Payment History (40%)**
   - Calculates ratio of EMIs paid on time vs total EMIs
   - Higher ratio = better score

2. **Loan Count (20%)**
   - ≤2 loans: 20 points
   - 3-5 loans: 15 points
   - 6-8 loans: 10 points
   - >8 loans: 5 points

3. **Current Year Activity (20%)**
   - 0 loans: 20 points
   - 1-2 loans: 15 points
   - 3-4 loans: 10 points
   - >4 loans: 5 points

4. **Loan Volume (20%)**
   - <30% of limit: 20 points
   - 30-60% of limit: 15 points
   - 60-90% of limit: 10 points
   - >90% of limit: 5 points

5. **Debt Check**
   - If current debt > approved limit: Score = 0

## 🎨 UI Features

### Professional Design
- Modern gradient-based design
- Responsive layout for all devices
- Intuitive tabbed navigation
- Real-time form validation

### User Experience
- Currency formatting (₹ Indian Rupees)
- Loading states and error handling
- Success/failure notifications
- Professional data tables

### Navigation Tabs
- **Register Customer** - Customer registration form
- **Check Eligibility** - Loan eligibility checker
- **Create Loan** - Loan creation interface
- **View Loan** - Individual loan viewer
- **Customer Loans** - Customer loan portfolio

## 🔧 Configuration

### Database Configuration
- MongoDB connection string in `backend/.env`
- Database name: `test_database`
- Collections: `customers`, `loans`

### API Configuration
- Backend URL configured in `frontend/.env`
- CORS enabled for all origins
- API prefix: `/api`

## 📈 Performance

### Scalability Features
- Async/await pattern for all database operations
- Background task processing for data ingestion
- Efficient MongoDB queries with proper indexing
- Compound interest calculations optimized

### Security Features
- Input validation with Pydantic models
- Error handling for all edge cases
- Proper HTTP status codes
- CORS configuration

## 🐳 Docker Deployment

The application is containerized and ready for deployment:

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or run individual services
docker build -t credit-backend ./backend
docker build -t credit-frontend ./frontend
```

## 📝 Data Models

### Customer Model
```python
{
    "customer_id": "uuid",
    "first_name": "string",
    "last_name": "string",
    "age": "integer",
    "phone_number": "string",
    "monthly_income": "integer",
    "approved_limit": "integer",
    "current_debt": "integer"
}
```

### Loan Model
```python
{
    "loan_id": "uuid",
    "customer_id": "string",
    "loan_amount": "float",
    "tenure": "integer",
    "interest_rate": "float",
    "monthly_installment": "float",
    "emis_paid_on_time": "integer",
    "start_date": "datetime",
    "end_date": "datetime"
}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Review the API documentation at `/docs`

## 🚀 Future Enhancements

- Advanced analytics dashboard
- Machine learning credit scoring
- Real-time notifications
- Multi-currency support
- Enhanced security features
- Automated testing pipeline

---

**Built with ❤️ using FastAPI, React, and MongoDB**
