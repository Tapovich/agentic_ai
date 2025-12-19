"""
Price Service
Handles cryptocurrency price data retrieval and management.
"""

from models import db


def get_latest_price(symbol):
    """
    Get the most recent price for a cryptocurrency symbol.
    
    Args:
        symbol (str): Cryptocurrency symbol (e.g., "BTCUSDT")
    
    Returns:
        dict: Price data with close_price, timestamp, etc.
        None: If no price data found
    
    Example:
        price = get_latest_price("BTCUSDT")
        print(f"Bitcoin price: ${price['close_price']}")
    """
    query = """
        SELECT * FROM price_history
        WHERE symbol = ?
        ORDER BY timestamp DESC
        LIMIT 1
    """
    
    price = db.fetch_one(query, (symbol,))
    return price


def get_current_prices(symbols):
    """
    Get current prices for multiple symbols.
    
    Args:
        symbols (list): List of cryptocurrency symbols
    
    Returns:
        dict: Dictionary mapping symbol to price
              {"BTCUSDT": 45600.00, "ETHUSDT": 2800.50}
    
    Example:
        prices = get_current_prices(["BTCUSDT", "ETHUSDT"])
        print(f"BTC: ${prices['BTCUSDT']}")
    """
    prices = {}
    
    for symbol in symbols:
        price_data = get_latest_price(symbol)
        if price_data:
            prices[symbol] = price_data['close_price']
        else:
            # Default prices if no data in database
            default_prices = {
                'BTCUSDT': 45600.00,
                'ETHUSDT': 2800.50,
                'BNBUSDT': 420.75,
                'SOLUSDT': 95.30,
                'ADAUSDT': 0.65
            }
            prices[symbol] = default_prices.get(symbol, 0)
    
    return prices


def get_price_history(symbol, limit=100):
    """
    Get historical price data for a symbol.
    
    Args:
        symbol (str): Cryptocurrency symbol
        limit (int): Number of records to retrieve
    
    Returns:
        list: List of price records, ordered by timestamp (oldest first)
    """
    query = """
        SELECT * FROM price_history
        WHERE symbol = ?
        ORDER BY timestamp DESC
        LIMIT ?
    """
    
    prices = db.fetch_all(query, (symbol, limit))
    
    if prices:
        # Reverse to get oldest first (needed for calculations)
        return list(reversed(prices))
    
    return []


def add_price_record(symbol, open_price, high_price, low_price, close_price, volume):
    """
    Add a new price record to the database.
    
    Args:
        symbol (str): Cryptocurrency symbol
        open_price (float): Opening price
        high_price (float): Highest price
        low_price (float): Lowest price
        close_price (float): Closing price
        volume (float): Trading volume
    
    Returns:
        int: Record ID if successful, None otherwise
    """
    query = """
        INSERT INTO price_history (symbol, timestamp, open_price, high_price, low_price, close_price, volume)
        VALUES (?, datetime('now'), ?, ?, ?, ?, ?)
    """
    
    return db.execute_query(query, (symbol, open_price, high_price, low_price, close_price, volume))

