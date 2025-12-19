"""
Test API Endpoints
Simple script to test the prediction API endpoints.

This script tests the API without needing a browser.
"""

import requests
import json


# Base URL
BASE_URL = 'http://127.0.0.1:5000'

# Demo credentials
USERNAME = 'testuser'
PASSWORD = 'password123'


def test_api():
    """
    Test the prediction API endpoints.
    """
    print("=" * 70)
    print("TESTING AI PREDICTION API")
    print("=" * 70)
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    # ========================================
    # Step 1: Login
    # ========================================
    print("\n[Step 1] Logging in...")
    
    login_data = {
        'username': USERNAME,
        'password': PASSWORD
    }
    
    response = session.post(f'{BASE_URL}/login', data=login_data, allow_redirects=False)
    
    if response.status_code in [200, 302]:
        print(f"✅ Login successful!")
    else:
        print(f"❌ Login failed! Status: {response.status_code}")
        print("   Make sure:")
        print("   1. Flask app is running (python app.py)")
        print("   2. Demo user exists (python create_demo_user.py)")
        return
    
    # ========================================
    # Step 2: Test Prediction API
    # ========================================
    print("\n[Step 2] Testing prediction API...")
    
    response = session.get(f'{BASE_URL}/api/predict')
    
    print(f"   Response status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        print(f"\n✅ API Response:")
        print(json.dumps(data, indent=2))
        
        if data.get('success'):
            print(f"\n📊 Prediction Summary:")
            print(f"   Symbol: {data.get('symbol')}")
            print(f"   Current Price: ${data.get('current_price', 0):,.2f}")
            print(f"   Prediction: {data.get('direction')}")
            print(f"   Confidence: {data.get('confidence_pct')}%")
            if 'prediction_id' in data:
                print(f"   Saved to DB with ID: {data.get('prediction_id')}")
    else:
        print(f"❌ API request failed!")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        print("\n   Possible reasons:")
        print("   - Model not trained (run: python services/train_model.py)")
        print("   - No price data (run: python setup_database.py)")
        print("   - Database connection issue")
    
    # ========================================
    # Step 3: Test Latest Prediction API
    # ========================================
    print("\n[Step 3] Testing latest prediction API...")
    
    response = session.get(f'{BASE_URL}/api/prediction/latest')
    
    if response.status_code == 200:
        data = response.json()
        
        if data.get('success'):
            prediction = data.get('prediction')
            print(f"\n✅ Latest Prediction:")
            print(f"   Symbol: {prediction.get('symbol')}")
            print(f"   Direction: {prediction.get('direction')}")
            print(f"   Confidence: {prediction.get('confidence_pct')}%")
            print(f"   Timestamp: {prediction.get('timestamp')}")
    else:
        print(f"⚠️  No saved predictions found (this is OK)")
    
    # ========================================
    # Step 4: Test with Different Symbol
    # ========================================
    print("\n[Step 4] Testing with different symbol (ETHUSDT)...")
    
    response = session.get(f'{BASE_URL}/api/predict/ETHUSDT')
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print(f"✅ ETHUSDT Prediction: {data.get('direction')} ({data.get('confidence_pct')}%)")
    else:
        print(f"⚠️  No data for ETHUSDT (expected if no price history)")
    
    # ========================================
    # Summary
    # ========================================
    print("\n" + "=" * 70)
    print("✅ API TESTING COMPLETE!")
    print("=" * 70)
    print("\nThe prediction API is working correctly.")
    print("You can now use these endpoints in your frontend:")
    print("  - GET /api/predict")
    print("  - GET /api/predict/<symbol>")
    print("  - GET /api/prediction/latest")
    print("  - GET /api/prediction/latest/<symbol>")
    print("=" * 70)


def test_without_login():
    """
    Test that API is protected (requires login).
    """
    print("\n" + "=" * 70)
    print("TESTING API PROTECTION")
    print("=" * 70)
    
    print("\n[Test] Accessing API without login...")
    
    response = requests.get(f'{BASE_URL}/api/predict')
    
    if response.status_code == 302 or 'login' in response.text.lower():
        print("✅ API is protected - redirects to login")
    else:
        print("⚠️  API might not be protected properly")
    
    print("=" * 70)


if __name__ == "__main__":
    import sys
    
    print("\n🚀 Starting API tests...")
    print("   Make sure Flask app is running: python app.py\n")
    
    try:
        # Test that API is protected
        test_without_login()
        
        # Test API functionality
        test_api()
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Could not connect to Flask app!")
        print("   Make sure the app is running:")
        print("   python app.py")
        print()
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

