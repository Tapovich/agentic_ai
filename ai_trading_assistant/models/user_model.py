"""
User Model
Functions for user management including registration and authentication.
"""

from werkzeug.security import generate_password_hash, check_password_hash
from models import db


def create_user(username, email, password_plain):
    """
    Create a new user account with hashed password.
    
    Args:
        username (str): Unique username
        email (str): User's email address
        password_plain (str): Plain text password (will be hashed)
    
    Returns:
        int: New user's ID if successful
        None: If user creation failed (e.g., duplicate username/email)
    
    Example:
        user_id = create_user("john_doe", "john@example.com", "mypassword123")
    """
    # Hash the password for security
    # NEVER store plain text passwords in the database!
    # Using pbkdf2:sha256 method for compatibility across all systems
    password_hash = generate_password_hash(password_plain, method='pbkdf2:sha256')
    
    # SQL query to insert new user
    # Initial balance is set to $10,000 by default in the database
    query = """
        INSERT INTO users (username, email, password_hash, balance)
        VALUES (?, ?, ?, 10000.00)
    """
    params = (username, email, password_hash)
    
    # Execute the query
    user_id = db.execute_query(query, params)
    
    if user_id:
        print(f"✅ User '{username}' created successfully! ID: {user_id}")
        return user_id
    else:
        print(f"❌ Failed to create user '{username}'. Username or email may already exist.")
        return None


def get_user_by_username(username):
    """
    Find a user by their username.
    Used for login and authentication.
    
    Args:
        username (str): The username to search for
    
    Returns:
        dict: User data (id, username, email, password_hash, balance, created_at)
        None: If user not found
    
    Example:
        user = get_user_by_username("john_doe")
        if user:
            print(f"Found user with ID: {user['id']}")
    """
    query = "SELECT * FROM users WHERE username = ?"
    user = db.fetch_one(query, (username,))
    
    return user


def get_user_by_id(user_id):
    """
    Find a user by their ID.
    Used to get user information from session.
    
    Args:
        user_id (int): The user's ID
    
    Returns:
        dict: User data
        None: If user not found
    
    Example:
        user = get_user_by_id(1)
    """
    query = "SELECT * FROM users WHERE id = ?"
    user = db.fetch_one(query, (user_id,))
    
    return user


def verify_password(password_plain, password_hash):
    """
    Check if a plain text password matches the hashed password.
    Used during login.
    
    Args:
        password_plain (str): Plain text password from login form
        password_hash (str): Hashed password from database
    
    Returns:
        bool: True if password is correct, False otherwise
    
    Example:
        is_correct = verify_password("mypassword123", user['password_hash'])
    """
    return check_password_hash(password_hash, password_plain)


def authenticate_user(username, password):
    """
    Authenticate a user by username and password.
    Combines get_user_by_username and verify_password.
    
    Args:
        username (str): Username
        password (str): Plain text password
    
    Returns:
        dict: User data if authentication successful
        None: If authentication failed
    
    Example:
        user = authenticate_user("john_doe", "mypassword123")
        if user:
            print(f"Login successful! Welcome {user['username']}")
        else:
            print("Invalid username or password")
    """
    # Get user from database
    user = get_user_by_username(username)
    
    # Check if user exists
    if user is None:
        return None
    
    # Verify password
    if verify_password(password, user['password_hash']):
        # Password is correct, return user data
        return user
    else:
        # Password is incorrect
        return None


def check_username_exists(username):
    """
    Check if a username already exists in the database.
    Used for registration validation.
    
    Args:
        username (str): Username to check
    
    Returns:
        bool: True if username exists, False otherwise
    
    Example:
        if check_username_exists("john_doe"):
            print("Username is already taken!")
    """
    user = get_user_by_username(username)
    return user is not None


def check_email_exists(email):
    """
    Check if an email already exists in the database.
    Used for registration validation.
    
    Args:
        email (str): Email to check
    
    Returns:
        bool: True if email exists, False otherwise
    
    Example:
        if check_email_exists("john@example.com"):
            print("Email is already registered!")
    """
    query = "SELECT * FROM users WHERE email = ?"
    user = db.fetch_one(query, (email,))
    return user is not None


def update_user_balance(user_id, new_balance):
    """
    Update a user's balance.
    Used after trades.
    
    Args:
        user_id (int): User's ID
        new_balance (float): New balance amount
    
    Returns:
        bool: True if successful, False otherwise
    
    Example:
        update_user_balance(1, 8500.00)
    """
    query = "UPDATE users SET balance = ? WHERE id = ?"
    result = db.execute_query(query, (new_balance, user_id))
    
    return result is not None

