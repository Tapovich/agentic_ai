"""
Database Usage Examples
This file contains practical examples of how to use the database helper functions.
These examples show common operations you'll need in the application.
"""

from models import db


# ============================================
# EXAMPLE 1: Creating a New User
# ============================================

def create_user(username, email, password_hash):
    """
    Create a new user in the database.
    
    Args:
        username (str): Unique username
        email (str): User's email address
        password_hash (str): Hashed password (never store plain text!)
    
    Returns:
        int: The new user's ID, or None if failed
    """
    query = """
        INSERT INTO users (username, email, password_hash, balance)
        VALUES (?, ?, ?, ?)
    """
    params = (username, email, password_hash, 10000.00)  # Start with $10,000
    
    user_id = db.execute_query(query, params)
    
    if user_id:
        print(f"✅ User created successfully! ID: {user_id}")
        return user_id
    else:
        print("❌ Failed to create user")
        return None


# ============================================
# EXAMPLE 2: Getting User by Username
# ============================================

def get_user_by_username(username):
    """
    Find a user by their username.
    
    Args:
        username (str): The username to search for
    
    Returns:
        dict: User data, or None if not found
    """
    query = "SELECT * FROM users WHERE username = ?"
    user = db.fetch_one(query, (username,))
    
    if user:
        print(f"✅ Found user: {user['username']}")
        return user
    else:
        print(f"❌ User '{username}' not found")
        return None


# ============================================
# EXAMPLE 3: Updating User Balance
# ============================================

def update_user_balance(user_id, new_balance):
    """
    Update a user's balance.
    
    Args:
        user_id (int): The user's ID
        new_balance (float): The new balance amount
    
    Returns:
        bool: True if successful, False otherwise
    """
    query = "UPDATE users SET balance = ? WHERE id = ?"
    result = db.execute_query(query, (new_balance, user_id))
    
    if result:
        print(f"✅ Balance updated to ${new_balance}")
        return True
    else:
        print("❌ Failed to update balance")
        return False


# ============================================
# EXAMPLE 4: Recording a Trade
# ============================================

def record_trade(user_id, symbol, side, quantity, price):
    """
    Record a buy or sell trade.
    
    Args:
        user_id (int): User making the trade
        symbol (str): Cryptocurrency symbol (e.g., "BTCUSDT")
        side (str): "BUY" or "SELL"
        quantity (float): Amount of crypto
        price (float): Price per unit
    
    Returns:
        int: Trade ID if successful, None otherwise
    """
    total_amount = quantity * price
    
    query = """
        INSERT INTO trades (user_id, symbol, side, quantity, price, total_amount)
        VALUES (?, ?, ?, ?, ?, ?)
    """
    params = (user_id, symbol, side, quantity, price, total_amount)
    
    trade_id = db.execute_query(query, params)
    
    if trade_id:
        print(f"✅ Trade recorded! ID: {trade_id}")
        return trade_id
    else:
        print("❌ Failed to record trade")
        return None


# ============================================
# EXAMPLE 5: Getting User's Trade History
# ============================================

def get_user_trades(user_id, limit=10):
    """
    Get recent trades for a user.
    
    Args:
        user_id (int): The user's ID
        limit (int): Maximum number of trades to return
    
    Returns:
        list: List of trade records
    """
    query = """
        SELECT * FROM trades
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
    """
    trades = db.fetch_all(query, (user_id, limit))
    
    if trades:
        print(f"✅ Found {len(trades)} trade(s)")
        return trades
    else:
        print("❌ No trades found")
        return []


# ============================================
# EXAMPLE 6: Getting Latest Price
# ============================================

def get_latest_price(symbol):
    """
    Get the most recent price for a cryptocurrency.
    
    Args:
        symbol (str): Cryptocurrency symbol (e.g., "BTCUSDT")
    
    Returns:
        dict: Price data, or None if not found
    """
    query = """
        SELECT * FROM price_history
        WHERE symbol = ?
        ORDER BY timestamp DESC
        LIMIT 1
    """
    price = db.fetch_one(query, (symbol,))
    
    if price:
        print(f"✅ Latest {symbol} price: ${price['close_price']}")
        return price
    else:
        print(f"❌ No price data found for {symbol}")
        return None


# ============================================
# EXAMPLE 7: Getting User's Portfolio
# ============================================

def get_user_portfolio(user_id):
    """
    Get all cryptocurrency holdings for a user.
    
    Args:
        user_id (int): The user's ID
    
    Returns:
        list: List of portfolio entries
    """
    query = """
        SELECT * FROM portfolio
        WHERE user_id = ?
    """
    portfolio = db.fetch_all(query, (user_id,))
    
    if portfolio:
        print(f"✅ Found {len(portfolio)} holding(s)")
        return portfolio
    else:
        print("❌ Portfolio is empty")
        return []


# ============================================
# EXAMPLE 8: Updating Portfolio
# ============================================

def update_portfolio(user_id, symbol, quantity, average_price):
    """
    Update or create a portfolio entry.
    This uses "ON DUPLICATE KEY UPDATE" to either insert or update.
    
    Args:
        user_id (int): The user's ID
        symbol (str): Cryptocurrency symbol
        quantity (float): New quantity
        average_price (float): Average purchase price
    
    Returns:
        bool: True if successful, False otherwise
    """
    query = """
        INSERT INTO portfolio (user_id, symbol, quantity, average_price)
        VALUES (?, ?, ?, ?)
        ON DUPLICATE KEY UPDATE
            quantity = ?,
            average_price = ?
    """
    params = (user_id, symbol, quantity, average_price, quantity, average_price)
    
    result = db.execute_query(query, params)
    
    if result:
        print(f"✅ Portfolio updated for {symbol}")
        return True
    else:
        print("❌ Failed to update portfolio")
        return False


# ============================================
# EXAMPLE 9: Getting Latest AI Prediction
# ============================================

def get_latest_prediction(symbol):
    """
    Get the most recent AI prediction for a cryptocurrency.
    
    Args:
        symbol (str): Cryptocurrency symbol
    
    Returns:
        dict: Prediction data with 'prediction_class' and 'confidence'
    """
    query = """
        SELECT * FROM predictions
        WHERE symbol = ?
        ORDER BY timestamp DESC
        LIMIT 1
    """
    prediction = db.fetch_one(query, (symbol,))
    
    if prediction:
        direction = "UP" if prediction['prediction_class'] == 1 else "DOWN"
        confidence = prediction['confidence'] * 100
        print(f"✅ Prediction: {direction} ({confidence:.1f}% confidence)")
        return prediction
    else:
        print(f"❌ No predictions found for {symbol}")
        return None


# ============================================
# EXAMPLE 10: Saving an AI Prediction
# ============================================

def save_prediction(symbol, prediction_class, confidence):
    """
    Save a new AI prediction to the database.
    
    Args:
        symbol (str): Cryptocurrency symbol
        prediction_class (int): 1 for UP, 0 for DOWN
        confidence (float): Confidence score (0.0 to 1.0)
    
    Returns:
        int: Prediction ID if successful, None otherwise
    """
    query = """
        INSERT INTO predictions (symbol, prediction_class, confidence)
        VALUES (?, ?, ?)
    """
    params = (symbol, prediction_class, confidence)
    
    prediction_id = db.execute_query(query, params)
    
    if prediction_id:
        print(f"✅ Prediction saved! ID: {prediction_id}")
        return prediction_id
    else:
        print("❌ Failed to save prediction")
        return None


# ============================================
# DEMO: Running the Examples
# ============================================

if __name__ == "__main__":
    print("=" * 60)
    print("Database Helper Examples - Demo")
    print("=" * 60)
    
    # Example: Get a user
    print("\n📌 Example: Getting a user by username")
    user = get_user_by_username("testuser")
    
    if user:
        # Example: Get user's trades
        print("\n📌 Example: Getting user's trade history")
        trades = get_user_trades(user['id'])
        
        # Example: Get user's portfolio
        print("\n📌 Example: Getting user's portfolio")
        portfolio = get_user_portfolio(user['id'])
    
    # Example: Get latest Bitcoin price
    print("\n📌 Example: Getting latest Bitcoin price")
    price = get_latest_price("BTCUSDT")
    
    # Example: Get latest prediction
    print("\n📌 Example: Getting latest AI prediction")
    prediction = get_latest_prediction("BTCUSDT")
    
    print("\n" + "=" * 60)
    print("✅ Examples completed!")
    print("=" * 60)

