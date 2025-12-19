"""
Database Setup Script
Run this script to create the database and all tables.

Usage:
    python setup_database.py
"""

import mysql.connector
from mysql.connector import Error
import config


def create_database_and_tables():
    """
    Create the database and all required tables by executing schema.sql
    """
    print("=" * 50)
    print("AI Trading Assistant - Database Setup")
    print("=" * 50)
    
    try:
        # First, connect without specifying a database to create it
        print("\n1. Connecting to MySQL server...")
        connection = mysql.connector.connect(
            host=config.DB_HOST,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            port=config.DB_PORT
        )
        
        if not connection.is_connected():
            print("✗ Failed to connect to MySQL server!")
            return False
        
        print("✓ Connected to MySQL server successfully!")
        
        cursor = connection.cursor()
        
        # Create database if it doesn't exist
        print(f"\n2. Creating database '{config.DB_NAME}'...")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {config.DB_NAME}")
        print(f"✓ Database '{config.DB_NAME}' ready!")
        
        # Use the database
        cursor.execute(f"USE {config.DB_NAME}")
        
        # Read and execute the schema.sql file
        print("\n3. Creating tables from schema.sql...")
        with open('schema.sql', 'r', encoding='utf-8') as file:
            sql_script = file.read()
        
        # Split the script into individual statements
        # Filter out comments and empty statements
        statements = []
        for statement in sql_script.split(';'):
            statement = statement.strip()
            # Skip empty statements and comment-only statements
            if statement and not all(line.strip().startswith('--') or line.strip() == '' 
                                    for line in statement.split('\n')):
                statements.append(statement)
        
        # Execute each statement
        for i, statement in enumerate(statements):
            try:
                # Skip CREATE DATABASE and USE statements (already handled)
                if 'CREATE DATABASE' in statement.upper() or statement.strip().upper().startswith('USE '):
                    continue
                
                cursor.execute(statement)
                
                # Print progress for CREATE TABLE statements
                if 'CREATE TABLE' in statement.upper():
                    # Extract table name
                    table_name = statement.split('CREATE TABLE')[1].split('(')[0].strip()
                    print(f"  ✓ Created table: {table_name}")
                    
            except Error as e:
                # Only print error if it's not about table already existing
                if 'already exists' not in str(e).lower():
                    print(f"  ⚠ Warning: {e}")
        
        connection.commit()
        print("\n4. Committing changes...")
        print("✓ All tables created successfully!")
        
        # Display table list
        print("\n5. Verifying tables...")
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        print("\nCreated tables:")
        for table in tables:
            print(f"  • {table[0]}")
        
        print("\n" + "=" * 50)
        print("✓ Database setup completed successfully!")
        print("=" * 50)
        print("\nYou can now run: python app.py")
        
        return True
        
    except Error as e:
        print(f"\n✗ Error during database setup: {e}")
        return False
        
    except FileNotFoundError:
        print("\n✗ Error: schema.sql file not found!")
        print("Make sure you're running this script from the ai_trading_assistant directory.")
        return False
        
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        return False
        
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
            print("\nDatabase connection closed.")


if __name__ == "__main__":
    # Run the setup
    success = create_database_and_tables()
    
    if not success:
        print("\n⚠ Setup failed! Please check your MySQL credentials in config.py")
        exit(1)

