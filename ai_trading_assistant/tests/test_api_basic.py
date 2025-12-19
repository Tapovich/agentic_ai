"""
Basic API Tests (TASK 45)

Tests critical API endpoints to ensure they:
1. Return correct HTTP status codes
2. Return valid JSON responses
3. Have required fields in responses
4. Handle errors gracefully

Run these tests before deployment to catch breaking changes.

Usage:
    python -m pytest tests/test_api_basic.py
    or
    python tests/test_api_basic.py
"""

import sys
import os

# Add parent directory to path so we can import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
import json
from app import app


class BasicAPITests(unittest.TestCase):
    """
    Test suite for critical API endpoints.
    
    These tests verify basic functionality without requiring:
    - Real user accounts
    - Live exchange connections
    - External API keys
    
    They test the "happy path" and basic error handling.
    """
    
    def setUp(self):
        """Set up test client before each test"""
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['SECRET_KEY'] = 'test-secret-key'
        self.client = self.app.test_client()
        
        print(f"\n{'='*70}")
        print(f"Running test: {self._testMethodName}")
        print(f"{'='*70}")
    
    def tearDown(self):
        """Clean up after each test"""
        pass
    
    # ========================================
    # Health Check Tests
    # ========================================
    
    def test_health_endpoint_exists(self):
        """Test that /api/health endpoint exists and returns JSON"""
        print("Testing: Health endpoint exists")
        
        response = self.client.get('/api/health')
        
        # Should return 200 or 500 (not 404)
        self.assertIn(response.status_code, [200, 500], 
                     "Health endpoint should exist (200 or 500, not 404)")
        
        # Should return JSON
        self.assertEqual(response.content_type, 'application/json',
                        "Health endpoint should return JSON")
        
        print(f"✅ Health endpoint exists: {response.status_code}")
    
    def test_health_response_structure(self):
        """Test that /api/health returns correct structure"""
        print("Testing: Health response structure")
        
        response = self.client.get('/api/health')
        data = json.loads(response.data)
        
        # Should have required fields
        self.assertIn('status', data, "Health response should have 'status'")
        self.assertIn('version', data, "Health response should have 'version'")
        self.assertIn('checks', data, "Health response should have 'checks'")
        
        # Checks should be a dict with expected keys
        checks = data['checks']
        self.assertIsInstance(checks, dict, "checks should be a dictionary")
        self.assertIn('db', checks, "checks should include 'db'")
        self.assertIn('price_service', checks, "checks should include 'price_service'")
        self.assertIn('indicator_service', checks, "checks should include 'indicator_service'")
        
        # Status should be one of the valid values
        self.assertIn(data['status'], ['ok', 'degraded', 'error'],
                     "status should be 'ok', 'degraded', or 'error'")
        
        print(f"✅ Health response structure valid")
        print(f"   Status: {data['status']}")
        print(f"   DB: {checks.get('db')}")
        print(f"   Price Service: {checks.get('price_service')}")
        print(f"   Indicator Service: {checks.get('indicator_service')}")
    
    # ========================================
    # Authentication Tests
    # ========================================
    
    def test_protected_routes_require_auth(self):
        """Test that protected routes return 401 or redirect when not authenticated"""
        print("Testing: Protected routes require authentication")
        
        protected_endpoints = [
            '/api/price/BTCUSDT',
            '/api/indicators/BTCUSDT',
            '/dashboard'
        ]
        
        for endpoint in protected_endpoints:
            response = self.client.get(endpoint)
            
            # Should redirect (302) or return 401/403
            self.assertIn(response.status_code, [302, 401, 403],
                         f"{endpoint} should require authentication")
            
            print(f"✅ {endpoint} requires auth: {response.status_code}")
    
    # ========================================
    # Public Route Tests
    # ========================================
    
    def test_root_route_exists(self):
        """Test that root route (/) exists"""
        print("Testing: Root route exists")
        
        response = self.client.get('/')
        
        # Should return 200 or 302 (redirect)
        self.assertIn(response.status_code, [200, 302],
                     "Root route should exist")
        
        print(f"✅ Root route exists: {response.status_code}")
    
    def test_login_page_exists(self):
        """Test that login page exists"""
        print("Testing: Login page exists")
        
        response = self.client.get('/login')
        
        # Should return 200
        self.assertEqual(response.status_code, 200,
                        "Login page should exist")
        
        print(f"✅ Login page exists: {response.status_code}")
    
    def test_register_page_exists(self):
        """Test that register page exists"""
        print("Testing: Register page exists")
        
        response = self.client.get('/register')
        
        # Should return 200
        self.assertEqual(response.status_code, 200,
                        "Register page should exist")
        
        print(f"✅ Register page exists: {response.status_code}")
    
    # ========================================
    # Error Handling Tests
    # ========================================
    
    def test_404_for_nonexistent_route(self):
        """Test that nonexistent routes return 404"""
        print("Testing: Nonexistent routes return 404")
        
        response = self.client.get('/this-route-does-not-exist')
        
        self.assertEqual(response.status_code, 404,
                        "Nonexistent routes should return 404")
        
        print(f"✅ Nonexistent route returns 404")
    
    # ========================================
    # Helper Methods
    # ========================================
    
    def _create_test_user_session(self):
        """
        Helper method to create an authenticated session for testing.
        
        Note: This is a simplified version for testing.
        In production, use proper authentication.
        """
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'test_user'
        
        print("✅ Created test user session")


class APIWithAuthTests(unittest.TestCase):
    """
    Test suite for API endpoints that require authentication.
    
    These tests simulate authenticated requests.
    """
    
    def setUp(self):
        """Set up test client with authentication"""
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['SECRET_KEY'] = 'test-secret-key'
        self.client = self.app.test_client()
        
        # Create authenticated session
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'test_user'
        
        print(f"\n{'='*70}")
        print(f"Running test (with auth): {self._testMethodName}")
        print(f"{'='*70}")
    
    # These tests are commented out because they require:
    # - Database with real data
    # - CCXT connection to exchanges
    # - Proper setup
    # 
    # Uncomment and run after setting up test database
    
    # def test_price_api_with_valid_symbol(self):
    #     """Test /api/price/<symbol> with valid symbol"""
    #     print("Testing: Price API with valid symbol")
    #     
    #     response = self.client.get('/api/price/BTCUSDT')
    #     
    #     # Should return 200 or 500 (service error, but not 404)
    #     self.assertIn(response.status_code, [200, 404, 500])
    #     
    #     if response.status_code == 200:
    #         data = json.loads(response.data)
    #         self.assertIn('price', data)
    #         self.assertIn('symbol', data)
    #         print(f"✅ Price API works: {data}")
    #     else:
    #         print(f"⚠️  Price API returned {response.status_code} (may need setup)")


def run_tests():
    """
    Run all tests and print results.
    
    Returns:
        int: 0 if all tests passed, 1 if any failed
    """
    print("\n" + "="*70)
    print("RUNNING API TESTS (TASK 45)")
    print("="*70)
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add all tests from BasicAPITests
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(BasicAPITests))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(APIWithAuthTests))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✅ ALL TESTS PASSED!")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        return 1


if __name__ == '__main__':
    exit_code = run_tests()
    sys.exit(exit_code)

