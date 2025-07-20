import requests
import json
import time
from datetime import datetime
import os


def get_backend_url():
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    return line.split('=')[1].strip()
    except:
        pass
    return "http://localhost:8001"

BASE_URL = get_backend_url()
API_URL = f"{BASE_URL}/api"

print(f"Testing Credit Approval System Backend at: {API_URL}")
print("=" * 80)

# Test Results Storage
test_results = {
    "passed": 0,
    "failed": 0,
    "errors": []
}

def log_test(test_name, success, message=""):
    """Log test results"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status}: {test_name}")
    if message:
        print(f"    {message}")
    
    if success:
        test_results["passed"] += 1
    else:
        test_results["failed"] += 1
        test_results["errors"].append(f"{test_name}: {message}")
    print()

def test_health_check():
    """Test GET /api/ endpoint"""
    try:
        response = requests.get(f"{API_URL}/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "message" in data and "Credit Approval System" in data["message"]:
                log_test("Health Check Endpoint", True, f"Response: {data}")
                return True
            else:
                log_test("Health Check Endpoint", False, f"Unexpected response: {data}")
                return False
        else:
            log_test("Health Check Endpoint", False, f"Status: {response.status_code}, Response: {response.text}")
            return False
    except Exception as e:
        log_test("Health Check Endpoint", False, f"Exception: {str(e)}")
        return False

def test_customer_registration():
    """Test POST /api/register endpoint with business logic validation"""
    test_cases = [
        {
            "name": "High Salary Customer (₹100,000/month)",
            "data": {
                "first_name": "Rajesh",
                "last_name": "Kumar",
                "age": 35,
                "monthly_income": 100000,
                "phone_number": "9876543210"
            },
            "expected_limit": 3600000  # 36 * 100000 = 3600000 (36 lakhs)
        },
        {
            "name": "Medium Salary Customer (₹50,000/month)",
            "data": {
                "first_name": "Priya",
                "last_name": "Sharma",
                "age": 28,
                "monthly_income": 50000,
                "phone_number": "9876543211"
            },
            "expected_limit": 1800000  # 36 * 50000 = 1800000 (18 lakhs)
        },
        {
            "name": "Low Salary Customer (₹25,000/month)",
            "data": {
                "first_name": "Amit",
                "last_name": "Singh",
                "age": 25,
                "monthly_income": 25000,
                "phone_number": "9876543212"
            },
            "expected_limit": 900000  # 36 * 25000 = 900000 (9 lakhs)
        }
    ]
    
    registered_customers = []
    
    for test_case in test_cases:
        try:
            response = requests.post(f"{API_URL}/register", json=test_case["data"], timeout=10)
            if response.status_code == 200:
                customer = response.json()
                
                # Validate customer_id is generated
                if "customer_id" not in customer:
                    log_test(f"Customer Registration - {test_case['name']}", False, "No customer_id generated")
                    continue
                
                # Validate approved_limit calculation
                if customer["approved_limit"] != test_case["expected_limit"]:
                    log_test(f"Customer Registration - {test_case['name']}", False, 
                           f"Expected limit: {test_case['expected_limit']}, Got: {customer['approved_limit']}")
                    continue
                
                # Validate all fields are present
                required_fields = ["customer_id", "first_name", "last_name", "age", "phone_number", "monthly_income", "approved_limit"]
                missing_fields = [field for field in required_fields if field not in customer]
                if missing_fields:
                    log_test(f"Customer Registration - {test_case['name']}", False, f"Missing fields: {missing_fields}")
                    continue
                
                registered_customers.append(customer)
                log_test(f"Customer Registration - {test_case['name']}", True, 
                       f"Customer ID: {customer['customer_id']}, Approved Limit: ₹{customer['approved_limit']:,}")
            else:
                log_test(f"Customer Registration - {test_case['name']}", False, 
                       f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            log_test(f"Customer Registration - {test_case['name']}", False, f"Exception: {str(e)}")
    
    return registered_customers

def test_loan_eligibility(customers):
    """Test POST /api/check-eligibility endpoint with credit scoring logic"""
    if not customers:
        log_test("Loan Eligibility Check", False, "No customers available for testing")
        return []
    
    eligibility_results = []
    
    # Test different loan scenarios
    test_scenarios = [
        {
            "name": "Small Loan Request (₹50,000)",
            "loan_amount": 50000,
            "interest_rate": 10.0,
            "tenure": 12
        },
        {
            "name": "Medium Loan Request (₹500,000)",
            "loan_amount": 500000,
            "interest_rate": 12.0,
            "tenure": 24
        },
        {
            "name": "Large Loan Request (₹1,000,000)",
            "loan_amount": 1000000,
            "interest_rate": 15.0,
            "tenure": 36
        },
        {
            "name": "High Interest Rate Loan (₹200,000)",
            "loan_amount": 200000,
            "interest_rate": 20.0,
            "tenure": 18
        }
    ]
    
    for customer in customers[:2]:  # Test with first 2 customers
        for scenario in test_scenarios:
            try:
                request_data = {
                    "customer_id": customer["customer_id"],
                    "loan_amount": scenario["loan_amount"],
                    "interest_rate": scenario["interest_rate"],
                    "tenure": scenario["tenure"]
                }
                
                response = requests.post(f"{API_URL}/check-eligibility", json=request_data, timeout=10)
                if response.status_code == 200:
                    eligibility = response.json()
                    
                    # Validate response structure
                    required_fields = ["customer_id", "approval", "interest_rate", "corrected_interest_rate", "tenure", "monthly_installment"]
                    missing_fields = [field for field in required_fields if field not in eligibility]
                    if missing_fields:
                        log_test(f"Loan Eligibility - {customer['first_name']} - {scenario['name']}", False, 
                               f"Missing fields: {missing_fields}")
                        continue
                    
                    # Validate business logic
                    approval_status = "Approved" if eligibility["approval"] else "Rejected"
                    interest_correction = ""
                    if eligibility["corrected_interest_rate"] != eligibility["interest_rate"]:
                        interest_correction = f" (Corrected from {eligibility['interest_rate']}% to {eligibility['corrected_interest_rate']}%)"
                    
                    eligibility_results.append({
                        "customer_id": customer["customer_id"],
                        "eligibility": eligibility,
                        "scenario": scenario
                    })
                    
                    log_test(f"Loan Eligibility - {customer['first_name']} - {scenario['name']}", True,
                           f"{approval_status}, EMI: ₹{eligibility['monthly_installment']:,.2f}{interest_correction}")
                else:
                    log_test(f"Loan Eligibility - {customer['first_name']} - {scenario['name']}", False,
                           f"Status: {response.status_code}, Response: {response.text}")
            except Exception as e:
                log_test(f"Loan Eligibility - {customer['first_name']} - {scenario['name']}", False, f"Exception: {str(e)}")
    
    return eligibility_results

def test_loan_creation(eligibility_results):
    """Test POST /api/create-loan endpoint"""
    if not eligibility_results:
        log_test("Loan Creation", False, "No eligibility results available for testing")
        return []
    
    created_loans = []
    
    # Test loan creation for approved eligibilities
    for result in eligibility_results[:3]:  # Test first 3 results
        if result["eligibility"]["approval"]:
            try:
                request_data = {
                    "customer_id": result["customer_id"],
                    "loan_amount": result["scenario"]["loan_amount"],
                    "interest_rate": result["scenario"]["interest_rate"],
                    "tenure": result["scenario"]["tenure"]
                }
                
                response = requests.post(f"{API_URL}/create-loan", json=request_data, timeout=10)
                if response.status_code == 200:
                    loan_response = response.json()
                    
                    # Validate response structure
                    required_fields = ["loan_id", "customer_id", "loan_approved", "message", "monthly_installment"]
                    missing_fields = [field for field in required_fields if field not in loan_response]
                    if missing_fields:
                        log_test(f"Loan Creation - Customer {result['customer_id'][:8]}...", False,
                               f"Missing fields: {missing_fields}")
                        continue
                    
                    if loan_response["loan_approved"] and loan_response["loan_id"]:
                        created_loans.append(loan_response)
                        log_test(f"Loan Creation - Customer {result['customer_id'][:8]}...", True,
                               f"Loan ID: {loan_response['loan_id'][:8]}..., EMI: ₹{loan_response['monthly_installment']:,.2f}")
                    else:
                        log_test(f"Loan Creation - Customer {result['customer_id'][:8]}...", False,
                               f"Loan not approved: {loan_response['message']}")
                else:
                    log_test(f"Loan Creation - Customer {result['customer_id'][:8]}...", False,
                           f"Status: {response.status_code}, Response: {response.text}")
            except Exception as e:
                log_test(f"Loan Creation - Customer {result['customer_id'][:8]}...", False, f"Exception: {str(e)}")
    
    return created_loans

def test_loan_viewing(created_loans, customers):
    """Test GET /api/view-loan/{loan_id} and GET /api/view-loans/{customer_id} endpoints"""
    
    # Test individual loan viewing
    for loan in created_loans[:2]:  # Test first 2 loans
        try:
            response = requests.get(f"{API_URL}/view-loan/{loan['loan_id']}", timeout=10)
            if response.status_code == 200:
                loan_details = response.json()
                
                # Validate response structure
                required_fields = ["loan_id", "customer", "loan_amount", "interest_rate", "monthly_installment", "tenure"]
                missing_fields = [field for field in required_fields if field not in loan_details]
                if missing_fields:
                    log_test(f"View Loan - {loan['loan_id'][:8]}...", False, f"Missing fields: {missing_fields}")
                    continue
                
                # Validate customer info in response
                customer_fields = ["id", "first_name", "last_name", "phone_number", "age"]
                missing_customer_fields = [field for field in customer_fields if field not in loan_details["customer"]]
                if missing_customer_fields:
                    log_test(f"View Loan - {loan['loan_id'][:8]}...", False, f"Missing customer fields: {missing_customer_fields}")
                    continue
                
                log_test(f"View Loan - {loan['loan_id'][:8]}...", True,
                       f"Amount: ₹{loan_details['loan_amount']:,}, Customer: {loan_details['customer']['first_name']} {loan_details['customer']['last_name']}")
            else:
                log_test(f"View Loan - {loan['loan_id'][:8]}...", False,
                       f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            log_test(f"View Loan - {loan['loan_id'][:8]}...", False, f"Exception: {str(e)}")
    
    # Test customer loans viewing
    for customer in customers[:2]:  # Test first 2 customers
        try:
            response = requests.get(f"{API_URL}/view-loans/{customer['customer_id']}", timeout=10)
            if response.status_code == 200:
                customer_loans = response.json()
                
                if isinstance(customer_loans, list):
                    if len(customer_loans) > 0:
                        # Validate loan structure
                        loan = customer_loans[0]
                        required_fields = ["loan_id", "loan_amount", "interest_rate", "monthly_installment", "repayments_left"]
                        missing_fields = [field for field in required_fields if field not in loan]
                        if missing_fields:
                            log_test(f"View Customer Loans - {customer['first_name']}", False, f"Missing fields: {missing_fields}")
                            continue
                        
                        log_test(f"View Customer Loans - {customer['first_name']}", True,
                               f"Found {len(customer_loans)} loan(s)")
                    else:
                        log_test(f"View Customer Loans - {customer['first_name']}", True, "No current loans found")
                else:
                    log_test(f"View Customer Loans - {customer['first_name']}", False, "Response is not a list")
            else:
                log_test(f"View Customer Loans - {customer['first_name']}", False,
                       f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            log_test(f"View Customer Loans - {customer['first_name']}", False, f"Exception: {str(e)}")

def test_data_ingestion():
    """Test POST /api/ingest-data endpoint"""
    try:
        response = requests.post(f"{API_URL}/ingest-data", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "message" in data and "ingestion" in data["message"].lower():
                log_test("Data Ingestion Endpoint", True, f"Response: {data}")
                return True
            else:
                log_test("Data Ingestion Endpoint", False, f"Unexpected response: {data}")
                return False
        else:
            log_test("Data Ingestion Endpoint", False, f"Status: {response.status_code}, Response: {response.text}")
            return False
    except Exception as e:
        log_test("Data Ingestion Endpoint", False, f"Exception: {str(e)}")
        return False

def test_edge_cases():
    """Test edge cases and error handling"""
    
    # Test invalid customer ID for eligibility check
    try:
        invalid_request = {
            "customer_id": "invalid-customer-id",
            "loan_amount": 100000,
            "interest_rate": 10.0,
            "tenure": 12
        }
        response = requests.post(f"{API_URL}/check-eligibility", json=invalid_request, timeout=10)
        if response.status_code == 404:
            log_test("Edge Case - Invalid Customer ID (Eligibility)", True, "Correctly returned 404 for invalid customer")
        else:
            log_test("Edge Case - Invalid Customer ID (Eligibility)", False, f"Expected 404, got {response.status_code}")
    except Exception as e:
        log_test("Edge Case - Invalid Customer ID (Eligibility)", False, f"Exception: {str(e)}")
    
    # Test invalid loan ID for loan viewing
    try:
        response = requests.get(f"{API_URL}/view-loan/invalid-loan-id", timeout=10)
        if response.status_code == 404:
            log_test("Edge Case - Invalid Loan ID", True, "Correctly returned 404 for invalid loan")
        else:
            log_test("Edge Case - Invalid Loan ID", False, f"Expected 404, got {response.status_code}")
    except Exception as e:
        log_test("Edge Case - Invalid Loan ID", False, f"Exception: {str(e)}")

def run_comprehensive_tests():
    """Run all backend tests in sequence"""
    print("🚀 Starting Comprehensive Backend Testing")
    print("=" * 80)
    
    # Test 1: Health Check
    print("1. Testing Health Check Endpoint...")
    health_ok = test_health_check()
    
    if not health_ok:
        print("❌ Health check failed. Cannot proceed with other tests.")
        return
    
    # Test 2: Customer Registration
    print("2. Testing Customer Registration...")
    customers = test_customer_registration()
    
    # Test 3: Loan Eligibility
    print("3. Testing Loan Eligibility Check...")
    eligibility_results = test_loan_eligibility(customers)
    
    # Test 4: Loan Creation
    print("4. Testing Loan Creation...")
    created_loans = test_loan_creation(eligibility_results)
    
    # Test 5: Loan Viewing
    print("5. Testing Loan Viewing...")
    test_loan_viewing(created_loans, customers)
    
    # Test 6: Data Ingestion
    print("6. Testing Data Ingestion...")
    test_data_ingestion()
    
    # Test 7: Edge Cases
    print("7. Testing Edge Cases...")
    test_edge_cases()
    
    # Final Results
    print("=" * 80)
    print("🏁 FINAL TEST RESULTS")
    print("=" * 80)
    print(f"✅ Tests Passed: {test_results['passed']}")
    print(f"❌ Tests Failed: {test_results['failed']}")
    print(f"📊 Success Rate: {(test_results['passed'] / (test_results['passed'] + test_results['failed']) * 100):.1f}%")
    
    if test_results['errors']:
        print("\n🔍 FAILED TESTS:")
        for error in test_results['errors']:
            print(f"   • {error}")
    
    print("\n" + "=" * 80)
    
    # Return summary for test_result.md update
    return {
        "total_tests": test_results['passed'] + test_results['failed'],
        "passed": test_results['passed'],
        "failed": test_results['failed'],
        "success_rate": (test_results['passed'] / (test_results['passed'] + test_results['failed']) * 100) if (test_results['passed'] + test_results['failed']) > 0 else 0,
        "errors": test_results['errors']
    }

if __name__ == "__main__":
    results = run_comprehensive_tests()