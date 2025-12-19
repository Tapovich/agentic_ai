"""
Database Connection Helper
Simple database connection and query functions for the AI Trading Assistant.

Note: This version uses SQLite by default for easy setup.
For MySQL, use the original MySQL implementation.
"""

import sqlite3
import os


# Using SQLite for easy setup (no MySQL required)
USE_SQLITE = True


def get_connection():
    """
    Create and return a connection to the database.
    
    Returns:
        connection object if successful, None if connection fails
    
    Example:
        conn = get_connection()
        if conn:
            print("Connected!")
    """
    try:
        # Using SQLite for easy setup
        db_path = 'ai_trading.db'
        connection = sqlite3.connect(db_path)
        connection.row_factory = sqlite3.Row  # Return rows as dictionaries
        return connection
            
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return None


def execute_query(query, params=None):
    """
    Execute a query that modifies data (INSERT, UPDATE, DELETE).
    Automatically commits the transaction.
    
    Args:
        query (str): SQL query to execute (e.g., "INSERT INTO users ...")
        params (tuple): Parameters for the query (optional)
    
    Returns:
        int: Last inserted ID for INSERT queries, or number of affected rows
        None: If query fails
    
    Example:
        # Insert a new user
        query = "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)"
        user_id = execute_query(query, ("john", "john@example.com", "hashed_password"))
    """
    connection = get_connection()
    
    # Return None if connection failed
    if connection is None:
        return None
    
    try:
        # Convert MySQL ? placeholders to SQLite ?
        query = query.replace('?', '?')
        
        cursor = connection.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        connection.commit()
        
        if cursor.lastrowid:
            return cursor.lastrowid
        else:
            return cursor.rowcount
        
    except Exception as e:
        print(f"❌ Query execution error: {e}")
        connection.rollback()
        return None
        
    finally:
        # Always close cursor and connection
        if 'cursor' in locals() and cursor:
            cursor.close()
        if connection:
            connection.close()


def fetch_all(query, params=None):
    """
    Execute a SELECT query and return all matching rows.
    
    Args:
        query (str): SELECT query (e.g., "SELECT * FROM users WHERE ...")
        params (tuple): Parameters for the query (optional)
    
    Returns:
        list: List of dictionaries, each representing one row
        None: If query fails
    
    Example:
        # Get all users
        query = "SELECT * FROM users"
        users = fetch_all(query)
        
        # Result: [{'id': 1, 'username': 'john', ...}, {'id': 2, ...}]
    """
    connection = get_connection()
    
    # Return None if connection failed
    if connection is None:
        return None
    
    try:
        # Convert MySQL ? to SQLite ?
        query = query.replace('?', '?')
        
        cursor = connection.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        rows = cursor.fetchall()
        
        # Convert to list of dictionaries
        results = [dict(row) for row in rows]
        
        return results
        
    except Exception as e:
        print(f"❌ Query error: {e}")
        return None
        
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if connection:
            connection.close()


def fetch_one(query, params=None):
    """
    Execute a SELECT query and return only the first matching row.
    
    Args:
        query (str): SELECT query (e.g., "SELECT * FROM users WHERE id = ?")
        params (tuple): Parameters for the query (optional)
    
    Returns:
        dict: Dictionary representing one row, or None if no match found
        None: If query fails
    
    Example:
        # Get one user by ID
        query = "SELECT * FROM users WHERE id = ?"
        user = fetch_one(query, (1,))
        
        # Result: {'id': 1, 'username': 'john', 'email': 'john@example.com', ...}
    """
    connection = get_connection()
    
    # Return None if connection failed
    if connection is None:
        return None
    
    try:
        # Convert MySQL ? to SQLite ?
        query = query.replace('?', '?')
        
        cursor = connection.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        row = cursor.fetchone()
        
        if row:
            return dict(row)
        return None
        
    except Exception as e:
        print(f"❌ Query error: {e}")
        return None
        
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if connection:
            connection.close()


# ============================================
# TEST FUNCTION (Optional)
# ============================================

def test_connection():
    """
    Test the database connection.
    This is a simple function to verify that database connection works.
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    print("Testing database connection...")
    connection = get_connection()
    
    if connection:
        print("✅ Database connection successful!")
        connection.close()
        return True
    else:
        print("❌ Database connection failed!")
        return False


# ============================================
# USAGE EXAMPLES (for learning)
# ============================================

"""
Example 1: Insert a new user
-------------------------------
query = "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)"
params = ("john_doe", "john@example.com", "hashed_password_here")
user_id = execute_query(query, params)
print(f"New user ID: {user_id}")


Example 2: Get all users
-------------------------
query = "SELECT * FROM users"
users = fetch_all(query)
for user in users:
    print(user['username'])


Example 3: Get one user by ID
------------------------------
query = "SELECT * FROM users WHERE id = ?"
user = fetch_one(query, (1,))
if user:
    print(f"Username: {user['username']}")


Example 4: Update user balance
-------------------------------
query = "UPDATE users SET balance = ? WHERE id = ?"
execute_query(query, (5000.00, 1))


Example 5: Delete a trade
--------------------------
query = "DELETE FROM trades WHERE id = ?"
execute_query(query, (10,))
"""

