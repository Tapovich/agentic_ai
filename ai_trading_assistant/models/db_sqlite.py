"""
SQLite Database Helper (Alternative to MySQL)
Simple database connection for quick setup without MySQL installation.
"""

import sqlite3
import os


def get_connection():
    """
    Create and return a connection to the SQLite database.
    
    Returns:
        connection object if successful, None if connection fails
    """
    try:
        # Database file location
        db_path = 'ai_trading.db'
        
        # Create connection
        connection = sqlite3.connect(db_path)
        connection.row_factory = sqlite3.Row  # Return rows as dictionaries
        
        return connection
            
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return None


def execute_query(query, params=None):
    """
    Execute a query that modifies data (INSERT, UPDATE, DELETE).
    
    Args:
        query (str): SQL query to execute
        params (tuple): Parameters for the query (optional)
    
    Returns:
        int: Last inserted ID for INSERT queries, or number of affected rows
        None: If query fails
    """
    connection = get_connection()
    
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
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def fetch_all(query, params=None):
    """
    Execute a SELECT query and return all matching rows.
    
    Args:
        query (str): SELECT query
        params (tuple): Parameters for the query (optional)
    
    Returns:
        list: List of dictionaries, each representing one row
        None: If query fails
    """
    connection = get_connection()
    
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
        
        # Convert Row objects to dictionaries
        results = [dict(row) for row in rows]
        
        return results
        
    except Exception as e:
        print(f"❌ Query error: {e}")
        return None
        
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def fetch_one(query, params=None):
    """
    Execute a SELECT query and return only the first matching row.
    
    Args:
        query (str): SELECT query
        params (tuple): Parameters for the query (optional)
    
    Returns:
        dict: Dictionary representing one row, or None if no match found
    """
    connection = get_connection()
    
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
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def test_connection():
    """
    Test the database connection.
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

