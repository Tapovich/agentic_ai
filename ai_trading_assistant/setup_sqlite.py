"""
SQLite Database Setup
Creates SQLite database with all tables for quick start.
No MySQL required!
"""

import sqlite3
import os


def setup_sqlite_database():
    """
    Create SQLite database and all required tables.
    """
    print("=" * 70)
    print("AI TRADING ASSISTANT - SQLite Database Setup")
    print("=" * 70)
    
    db_path = 'ai_trading.db'
    
    # Remove old database if exists
    if os.path.exists(db_path):
        print(f"\n⚠️  Removing existing database: {db_path}")
        os.remove(db_path)
    
    print(f"\n[1] Creating SQLite database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("[2] Creating tables...")
    
    # Users table
    cursor.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            balance REAL DEFAULT 10000.00,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("  ✅ Created table: users")
    
    # Price history table
    cursor.execute("""
        CREATE TABLE price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            open_price REAL NOT NULL,
            high_price REAL NOT NULL,
            low_price REAL NOT NULL,
            close_price REAL NOT NULL,
            volume REAL DEFAULT 0
        )
    """)
    print("  ✅ Created table: price_history")
    
    # Predictions table
    cursor.execute("""
        CREATE TABLE predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            prediction_class INTEGER NOT NULL,
            confidence REAL NOT NULL
        )
    """)
    print("  ✅ Created table: predictions")
    
    # Portfolio table
    cursor.execute("""
        CREATE TABLE portfolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            quantity REAL NOT NULL,
            average_price REAL NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE (user_id, symbol)
        )
    """)
    print("  ✅ Created table: portfolio")
    
    # Trades table
    cursor.execute("""
        CREATE TABLE trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            side TEXT NOT NULL,
            quantity REAL NOT NULL,
            price REAL NOT NULL,
            total_amount REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    print("  ✅ Created table: trades")
    
    print("\n[3] Inserting sample data...")
    
    # Insert sample price data
    cursor.execute("""
        INSERT INTO price_history (symbol, timestamp, open_price, high_price, low_price, close_price, volume)
        VALUES ('BTCUSDT', '2025-11-13 09:00:00', 45000.00, 45500.00, 44800.00, 45200.00, 1250.50)
    """)
    cursor.execute("""
        INSERT INTO price_history (symbol, timestamp, open_price, high_price, low_price, close_price, volume)
        VALUES ('BTCUSDT', '2025-11-13 10:00:00', 45200.00, 45800.00, 45100.00, 45600.00, 1380.75)
    """)
    cursor.execute("""
        INSERT INTO price_history (symbol, timestamp, open_price, high_price, low_price, close_price, volume)
        VALUES ('BTCUSDT', '2025-11-13 11:00:00', 45600.00, 46000.00, 45400.00, 45900.00, 1520.25)
    """)
    print("  ✅ Inserted sample price data")
    
    conn.commit()
    
    print("\n[4] Database setup complete!")
    print("=" * 70)
    print("✅ SQLite database created successfully!")
    print("=" * 70)
    print(f"\nDatabase file: {db_path}")
    print("Tables created: users, price_history, predictions, portfolio, trades")
    print("\nYou can now:")
    print("  1. Create a demo user: python3 create_demo_user.py")
    print("  2. Run the app: python3 app.py")
    print("  3. Register at: http://127.0.0.1:5000/register")
    print("=" * 70)
    
    conn.close()


if __name__ == "__main__":
    setup_sqlite_database()

