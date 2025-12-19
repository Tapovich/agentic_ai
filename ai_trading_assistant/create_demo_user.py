"""
Create Demo User
This script creates a demo user for testing the application.

Usage:
    python create_demo_user.py
"""

from models import user_model

def create_demo_user():
    """
    Create a demo user with username 'testuser' and password 'password123'
    """
    print("=" * 60)
    print("Creating Demo User")
    print("=" * 60)
    
    # Demo user credentials
    username = "testuser"
    email = "test@example.com"
    password = "password123"
    
    # Check if user already exists
    print(f"\n1. Checking if user '{username}' already exists...")
    if user_model.check_username_exists(username):
        print(f"⚠️  User '{username}' already exists in the database.")
        print(f"\nYou can use these credentials to log in:")
        print(f"   Username: {username}")
        print(f"   Password: {password}")
        return
    
    # Create the demo user
    print(f"2. Creating user '{username}'...")
    user_id = user_model.create_user(username, email, password)
    
    if user_id:
        print(f"\n✅ Demo user created successfully!")
        print(f"\n" + "=" * 60)
        print("Demo User Credentials:")
        print("=" * 60)
        print(f"Username: {username}")
        print(f"Password: {password}")
        print(f"Email: {email}")
        print(f"Initial Balance: $10,000.00")
        print("=" * 60)
        print(f"\n💡 Use these credentials to log in to the application!")
    else:
        print(f"\n❌ Failed to create demo user.")
        print(f"   This might be because:")
        print(f"   - The database is not set up (run setup_database.py first)")
        print(f"   - The email '{email}' is already registered")


if __name__ == "__main__":
    create_demo_user()

