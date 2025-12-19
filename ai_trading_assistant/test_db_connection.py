"""
Test Database Connection
Simple script to test if the database connection works.

Usage:
    python test_db_connection.py
"""

# Import the database helper functions
from models import db


def main():
    """
    Main function to test database connection and basic queries.
    """
    print("=" * 60)
    print("AI Trading Assistant - Database Connection Test")
    print("=" * 60)
    
    # Test 1: Connection Test
    print("\n[Test 1] Testing database connection...")
    print("-" * 60)
    if db.test_connection():
        print("✅ Test 1 PASSED: Database connection works!")
    else:
        print("❌ Test 1 FAILED: Cannot connect to database")
        print("\n💡 Make sure:")
        print("   1. MySQL server is running")
        print("   2. Config.py has correct credentials")
        print("   3. Database 'ai_trading_db' exists (run setup_database.py)")
        return
    
    # Test 2: Fetch All Users
    print("\n[Test 2] Fetching all users from database...")
    print("-" * 60)
    query = "SELECT * FROM users"
    users = db.fetch_all(query)
    
    if users is not None:
        print(f"✅ Test 2 PASSED: Found {len(users)} user(s)")
        for user in users:
            print(f"   - User ID: {user['id']}, Username: {user['username']}, Balance: ${user['balance']}")
    else:
        print("❌ Test 2 FAILED: Could not fetch users")
    
    # Test 3: Fetch One User
    print("\n[Test 3] Fetching one user (ID = 1)...")
    print("-" * 60)
    query = "SELECT * FROM users WHERE id = %s"
    user = db.fetch_one(query, (1,))
    
    if user:
        print("✅ Test 3 PASSED: User found")
        print(f"   Username: {user['username']}")
        print(f"   Email: {user['email']}")
        print(f"   Balance: ${user['balance']}")
    else:
        print("⚠️  Test 3: No user with ID = 1 found (this is OK if no data)")
    
    # Test 4: Fetch Price History
    print("\n[Test 4] Fetching price history...")
    print("-" * 60)
    query = "SELECT * FROM price_history LIMIT 5"
    prices = db.fetch_all(query)
    
    if prices is not None:
        print(f"✅ Test 4 PASSED: Found {len(prices)} price record(s)")
        for price in prices:
            print(f"   - {price['symbol']}: ${price['close_price']} at {price['timestamp']}")
    else:
        print("❌ Test 4 FAILED: Could not fetch price history")
    
    # Test 5: Count Tables
    print("\n[Test 5] Checking database tables...")
    print("-" * 60)
    query = "SHOW TABLES"
    tables = db.fetch_all(query)
    
    if tables:
        print(f"✅ Test 5 PASSED: Found {len(tables)} table(s)")
        for table in tables:
            table_name = list(table.values())[0]
            print(f"   - {table_name}")
    else:
        print("❌ Test 5 FAILED: Could not list tables")
    
    # Final Summary
    print("\n" + "=" * 60)
    print("✅ All basic database tests completed!")
    print("=" * 60)
    print("\n💡 Your database connection is working correctly.")
    print("   You can now use these functions in your Flask app:")
    print("   - db.get_connection()")
    print("   - db.execute_query(query, params)")
    print("   - db.fetch_all(query, params)")
    print("   - db.fetch_one(query, params)")
    print()


if __name__ == "__main__":
    main()

