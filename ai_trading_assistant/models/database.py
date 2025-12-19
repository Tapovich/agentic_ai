"""
Database Connection Module
Provides utility functions to connect to MySQL database
and execute queries safely.
"""

import mysql.connector
from mysql.connector import Error
import config


def get_db_connection():
    """
    Create and return a connection to the MySQL database.
    
    Returns:
        connection: MySQL connection object if successful, None if failed
    """
    try:
        connection = mysql.connector.connect(
            host=config.DB_HOST,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME,
            port=config.DB_PORT
        )
        
        if connection.is_connected():
            return connection
            
    except Error as e:
        print(f"Error connecting to MySQL database: {e}")
        return None


def execute_query(query, params=None, fetch_one=False, fetch_all=False, commit=False):
    """
    Execute a SQL query with parameters.
    
    Args:
        query (str): SQL query to execute
        params (tuple): Parameters for the query (optional)
        fetch_one (bool): If True, return one row
        fetch_all (bool): If True, return all rows
        commit (bool): If True, commit the transaction (for INSERT, UPDATE, DELETE)
    
    Returns:
        Result of the query (depends on fetch_one/fetch_all flags)
        For INSERT queries with commit=True, returns the last inserted ID
    """
    connection = get_db_connection()
    
    if connection is None:
        return None
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, params or ())
        
        if commit:
            connection.commit()
            # Return the last inserted ID for INSERT queries
            return cursor.lastrowid
        
        if fetch_one:
            result = cursor.fetchone()
            return result
        
        if fetch_all:
            result = cursor.fetchall()
            return result
        
        return True
        
    except Error as e:
        print(f"Error executing query: {e}")
        if commit:
            connection.rollback()
        return None
        
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def init_database():
    """
    Initialize the database by creating tables if they don't exist.
    This function reads and executes the schema.sql file.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Read the schema.sql file
        with open('schema.sql', 'r') as file:
            sql_script = file.read()
        
        # Split into individual statements
        statements = sql_script.split(';')
        
        connection = get_db_connection()
        if connection is None:
            return False
        
        cursor = connection.cursor()
        
        # Execute each statement
        for statement in statements:
            statement = statement.strip()
            if statement and not statement.startswith('--'):
                try:
                    cursor.execute(statement)
                except Error as e:
                    print(f"Warning executing statement: {e}")
        
        connection.commit()
        print("Database initialized successfully!")
        return True
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False
        
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


def test_connection():
    """
    Test the database connection.
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    connection = get_db_connection()
    if connection:
        print("✓ Database connection successful!")
        connection.close()
        return True
    else:
        print("✗ Database connection failed!")
        return False

