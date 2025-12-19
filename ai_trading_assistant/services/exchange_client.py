"""
Cryptocurrency Exchange Client
Unified connector for multiple centralized exchanges (CEX) using CCXT library.

CCXT (CryptoCurrency eXchange Trading) is a library that provides a unified API
to connect to 100+ cryptocurrency exchanges including Binance, Bybit, OKX, etc.

Educational Purpose:
-------------------
This module demonstrates how to:
- Connect to multiple exchanges with one codebase
- Fetch account balances
- Get open positions
- Place market orders
- Handle different exchange APIs uniformly

⚠️ IMPORTANT SECURITY NOTE:
In a real production system, API keys and secrets must be:
- Stored encrypted in a secure database
- Never committed to git repositories
- Accessed via environment variables or secret management systems
- Protected with proper access controls

For this university project, we're demonstrating the concept.
"""

import ccxt
from typing import Dict, List, Optional


# ============================================
# EXCHANGE CLIENT CREATION
# ============================================

def create_exchange_client(exchange_name, api_key=None, api_secret=None, is_testnet=False):
    """
    Create a unified exchange client for supported CEX platforms.
    
    Supported Exchanges:
        - Binance: World's largest crypto exchange
        - Bybit: Popular derivatives exchange
        - OKX: Major exchange with spot and futures
        - MEXC: Wide selection of altcoins
        - BingX: Copy trading and derivatives
    
    Args:
        exchange_name (str): Name of exchange ("binance", "bybit", "okx", "mexc", "bingx")
        api_key (str, optional): API key for authentication
        api_secret (str, optional): API secret for authentication
        is_testnet (bool): If True, use testnet/sandbox mode for safe testing
    
    Returns:
        ccxt.Exchange: Initialized exchange client
        None: If exchange not supported or error occurred
    
    Example:
        # Create Binance client for testnet
        client = create_exchange_client("binance", is_testnet=True)
        
        # Create with API credentials
        client = create_exchange_client(
            "binance",
            api_key="your_api_key",
            api_secret="your_api_secret"
        )
    
    Security Warning:
        Never hardcode API keys in your code!
        Use environment variables or secure storage.
    """
    
    # Normalize exchange name to lowercase
    exchange_name = exchange_name.lower().strip()
    
    # Map of supported exchanges to their ccxt classes
    exchange_classes = {
        'binance': ccxt.binance,
        'bybit': ccxt.bybit,
        'okx': ccxt.okx,
        'mexc': ccxt.mexc,
        'bingx': ccxt.bingx
    }
    
    # Check if exchange is supported
    if exchange_name not in exchange_classes:
        print(f"❌ Error: Exchange '{exchange_name}' is not supported")
        print(f"   Supported exchanges: {', '.join(exchange_classes.keys())}")
        return None
    
    try:
        # Get the exchange class
        ExchangeClass = exchange_classes[exchange_name]
        
        # Create configuration dictionary
        config = {
            'enableRateLimit': True,  # Important: prevents rate limit bans
        }
        
        # Add API credentials if provided
        if api_key and api_secret:
            config['apiKey'] = api_key
            config['secret'] = api_secret
        
        # Initialize exchange
        exchange = ExchangeClass(config)
        
        # Configure testnet mode if requested
        if is_testnet:
            # Different exchanges use different methods for testnet
            if exchange_name in ['binance', 'bybit', 'okx']:
                exchange.set_sandbox_mode(True)
                print(f"✅ {exchange_name.capitalize()} client created (TESTNET mode)")
            else:
                print(f"⚠️  {exchange_name.capitalize()} may not support testnet")
                print(f"✅ {exchange_name.capitalize()} client created (production mode)")
        else:
            print(f"✅ {exchange_name.capitalize()} client created")
        
        return exchange
        
    except Exception as e:
        print(f"❌ Error creating {exchange_name} client: {e}")
        return None


# ============================================
# ACCOUNT INFORMATION
# ============================================

def get_balances(exchange):
    """
    Get account balances from exchange.
    
    Returns balances for all assets (cryptocurrencies) in your account.
    
    Args:
        exchange: ccxt exchange client instance
    
    Returns:
        dict: Dictionary with balance information
              {
                  "USDT": {"free": 1000.00, "used": 200.00, "total": 1200.00},
                  "BTC": {"free": 0.5, "used": 0.1, "total": 0.6},
                  ...
              }
              Returns None if error occurs
    
    Example:
        client = create_exchange_client("binance", api_key, api_secret)
        balances = get_balances(client)
        
        print(f"Free USDT: ${balances['USDT']['free']}")
        print(f"Total BTC: {balances['BTC']['total']}")
    
    Balance Types:
        - free: Available for trading
        - used: Locked in open orders
        - total: free + used
    """
    
    if not exchange:
        print("❌ Error: Exchange client is None")
        return None
    
    try:
        # Fetch balance from exchange
        # This makes an API call to the exchange
        balance_response = exchange.fetch_balance()
        
        # Extract balance information
        # CCXT returns balances in a standard format across all exchanges
        balances = {}
        
        for currency, balance_info in balance_response.items():
            if isinstance(balance_info, dict) and 'free' in balance_info:
                # Only include currencies with non-zero balance
                if balance_info.get('total', 0) > 0:
                    balances[currency] = {
                        'free': balance_info.get('free', 0),
                        'used': balance_info.get('used', 0),
                        'total': balance_info.get('total', 0)
                    }
        
        print(f"✅ Retrieved balances for {len(balances)} assets")
        return balances
        
    except ccxt.AuthenticationError as e:
        print(f"❌ Authentication Error: Invalid API key or secret")
        print(f"   {e}")
        return None
        
    except ccxt.NetworkError as e:
        print(f"❌ Network Error: Cannot connect to exchange")
        print(f"   {e}")
        return None
        
    except Exception as e:
        print(f"❌ Error fetching balances: {e}")
        return None


# ============================================
# POSITION MANAGEMENT
# ============================================

def get_open_positions(exchange):
    """
    Get open positions from exchange (for futures/margin trading).
    
    Note: This only works for exchanges that support futures trading.
    Spot trading doesn't have "positions" - use get_balances() instead.
    
    Args:
        exchange: ccxt exchange client instance
    
    Returns:
        list: List of open position dictionaries
              [
                  {
                      "symbol": "BTC/USDT:USDT",
                      "side": "long",
                      "size": 0.5,
                      "entry_price": 45000.00,
                      "current_price": 46000.00,
                      "unrealized_pnl": 500.00
                  },
                  ...
              ]
              Returns empty list if no positions or not supported
    
    Example:
        client = create_exchange_client("bybit", api_key, api_secret)
        positions = get_open_positions(client)
        
        for pos in positions:
            print(f"{pos['symbol']}: {pos['side']} {pos['size']} @ ${pos['entry_price']}")
    """
    
    if not exchange:
        print("❌ Error: Exchange client is None")
        return []
    
    try:
        # Check if exchange supports fetching positions
        if not hasattr(exchange, 'fetch_positions'):
            print(f"ℹ️  {exchange.id} does not support positions (spot trading only)")
            return []
        
        # Fetch positions from exchange
        positions_response = exchange.fetch_positions()
        
        # Format positions in a simplified structure
        positions = []
        
        for pos in positions_response:
            # Only include positions with non-zero size
            if pos.get('contracts', 0) > 0 or pos.get('contractSize', 0) > 0:
                positions.append({
                    'symbol': pos.get('symbol', 'Unknown'),
                    'side': pos.get('side', 'Unknown'),  # 'long' or 'short'
                    'size': pos.get('contracts', 0),
                    'entry_price': pos.get('entryPrice', 0),
                    'current_price': pos.get('markPrice', 0),
                    'unrealized_pnl': pos.get('unrealizedPnl', 0),
                    'leverage': pos.get('leverage', 1)
                })
        
        print(f"✅ Retrieved {len(positions)} open position(s)")
        return positions
        
    except ccxt.AuthenticationError as e:
        print(f"❌ Authentication Error: {e}")
        return []
        
    except AttributeError:
        # Exchange doesn't support positions
        print(f"ℹ️  {exchange.id} does not support position fetching")
        return []
        
    except Exception as e:
        print(f"❌ Error fetching positions: {e}")
        return []


# ============================================
# ORDER PLACEMENT
# ============================================

def place_market_order(exchange, symbol, side, amount):
    """
    Place a market order on the exchange.
    
    Market Order: Executes immediately at the current market price.
    
    Args:
        exchange: ccxt exchange client instance
        symbol (str): Trading pair (e.g., "BTC/USDT", "ETH/USDT")
        side (str): "buy" or "sell"
        amount (float): Amount to trade (in base currency)
    
    Returns:
        dict: Order result with order_id, price, status, etc.
              Returns None if error occurs
    
    Example:
        client = create_exchange_client("binance", api_key, api_secret)
        
        # Buy 0.01 BTC
        order = place_market_order(client, "BTC/USDT", "buy", 0.01)
        
        if order:
            print(f"Order ID: {order['id']}")
            print(f"Filled price: ${order['average']}")
            print(f"Status: {order['status']}")
    
    ⚠️ WARNING:
        - This places a REAL order on the exchange!
        - Make sure you're using testnet for testing
        - Double-check symbol, side, and amount
        - Understand you can lose money in real trading
    """
    
    if not exchange:
        print("❌ Error: Exchange client is None")
        return None
    
    # Validate inputs
    if not symbol or not side or not amount:
        print("❌ Error: Missing required parameters (symbol, side, amount)")
        return None
    
    side = side.lower()
    if side not in ['buy', 'sell']:
        print(f"❌ Error: Invalid side '{side}'. Must be 'buy' or 'sell'")
        return None
    
    if amount <= 0:
        print(f"❌ Error: Amount must be positive (got {amount})")
        return None
    
    try:
        print(f"\n{'='*70}")
        print(f"Placing Market Order")
        print(f"{'='*70}")
        print(f"Exchange: {exchange.id}")
        print(f"Symbol: {symbol}")
        print(f"Side: {side.upper()}")
        print(f"Amount: {amount}")
        print(f"{'='*70}\n")
        
        # Place market order
        # Market orders execute at best available price
        order = exchange.create_market_order(
            symbol=symbol,
            side=side,
            amount=amount
        )
        
        print(f"✅ Order placed successfully!")
        print(f"   Order ID: {order.get('id', 'N/A')}")
        print(f"   Status: {order.get('status', 'N/A')}")
        print(f"   Filled: {order.get('filled', 0)}")
        print(f"   Average Price: ${order.get('average', 0)}")
        
        return order
        
    except ccxt.InsufficientFunds as e:
        print(f"❌ Insufficient Funds: Not enough balance to execute order")
        print(f"   {e}")
        return None
        
    except ccxt.InvalidOrder as e:
        print(f"❌ Invalid Order: Order parameters are incorrect")
        print(f"   {e}")
        return None
        
    except ccxt.AuthenticationError as e:
        print(f"❌ Authentication Error: Invalid API credentials")
        print(f"   {e}")
        return None
        
    except ccxt.NetworkError as e:
        print(f"❌ Network Error: Cannot connect to exchange")
        print(f"   {e}")
        return None
        
    except Exception as e:
        print(f"❌ Error placing order: {e}")
        return None


# ============================================
# MARKET DATA
# ============================================

def get_ticker(exchange, symbol):
    """
    Get current market ticker data for a symbol.
    
    Ticker includes: current price, 24h high/low, volume, etc.
    
    Args:
        exchange: ccxt exchange client instance
        symbol (str): Trading pair (e.g., "BTC/USDT")
    
    Returns:
        dict: Ticker data with price, volume, change, etc.
    
    Example:
        client = create_exchange_client("binance")
        ticker = get_ticker(client, "BTC/USDT")
        
        print(f"Current Price: ${ticker['last']}")
        print(f"24h High: ${ticker['high']}")
        print(f"24h Low: ${ticker['low']}")
        print(f"24h Volume: {ticker['volume']}")
    """
    
    if not exchange:
        return None
    
    try:
        ticker = exchange.fetch_ticker(symbol)
        
        return {
            'symbol': ticker.get('symbol', symbol),
            'last': ticker.get('last', 0),           # Current price
            'bid': ticker.get('bid', 0),             # Highest buy order
            'ask': ticker.get('ask', 0),             # Lowest sell order
            'high': ticker.get('high', 0),           # 24h high
            'low': ticker.get('low', 0),             # 24h low
            'volume': ticker.get('volume', 0),       # 24h volume
            'change': ticker.get('change', 0),       # 24h price change
            'percentage': ticker.get('percentage', 0) # 24h change %
        }
        
    except Exception as e:
        print(f"❌ Error fetching ticker: {e}")
        return None


def get_order_book(exchange, symbol, limit=20):
    """
    Get order book (bids and asks) for a symbol.
    
    Order book shows all pending buy and sell orders.
    
    Args:
        exchange: ccxt exchange client instance
        symbol (str): Trading pair
        limit (int): Number of orders to fetch per side
    
    Returns:
        dict: Order book with bids and asks
    """
    
    if not exchange:
        return None
    
    try:
        order_book = exchange.fetch_order_book(symbol, limit)
        
        return {
            'bids': order_book.get('bids', []),  # Buy orders [[price, amount], ...]
            'asks': order_book.get('asks', []),  # Sell orders [[price, amount], ...]
            'timestamp': order_book.get('timestamp', None)
        }
        
    except Exception as e:
        print(f"❌ Error fetching order book: {e}")
        return None


# ============================================
# EXCHANGE INFORMATION
# ============================================

def get_exchange_info(exchange):
    """
    Get basic information about the exchange.
    
    Args:
        exchange: ccxt exchange client instance
    
    Returns:
        dict: Exchange information
    """
    
    if not exchange:
        return None
    
    return {
        'id': exchange.id,
        'name': exchange.name,
        'has_sandbox': exchange.has.get('sandbox', False),
        'has_spot': exchange.has.get('spot', False),
        'has_margin': exchange.has.get('margin', False),
        'has_futures': exchange.has.get('futures', False),
        'rate_limit': exchange.rateLimit,
        'countries': exchange.countries if hasattr(exchange, 'countries') else []
    }


def list_available_markets(exchange, quote='USDT'):
    """
    List all available trading pairs on the exchange.
    
    Args:
        exchange: ccxt exchange client instance
        quote (str): Quote currency to filter by (e.g., "USDT", "BTC")
    
    Returns:
        list: List of symbol strings
    
    Example:
        client = create_exchange_client("binance")
        usdt_pairs = list_available_markets(client, "USDT")
        print(usdt_pairs)  # ["BTC/USDT", "ETH/USDT", ...]
    """
    
    if not exchange:
        return []
    
    try:
        markets = exchange.load_markets()
        
        # Filter by quote currency if specified
        if quote:
            symbols = [symbol for symbol in markets.keys() if symbol.endswith(f'/{quote}')]
        else:
            symbols = list(markets.keys())
        
        return sorted(symbols)
        
    except Exception as e:
        print(f"❌ Error loading markets: {e}")
        return []


# ============================================
# UTILITY FUNCTIONS
# ============================================

def test_connection(exchange):
    """
    Test if connection to exchange works.
    
    Args:
        exchange: ccxt exchange client instance
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    
    if not exchange:
        return False
    
    try:
        # Try to fetch exchange status or a simple ticker
        exchange.fetch_status()
        print(f"✅ Connection to {exchange.id} successful!")
        return True
        
    except AttributeError:
        # Some exchanges don't have fetch_status, try ticker instead
        try:
            exchange.fetch_ticker('BTC/USDT')
            print(f"✅ Connection to {exchange.id} successful!")
            return True
        except:
            pass
    
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


def get_minimum_order_size(exchange, symbol):
    """
    Get minimum order size for a trading pair.
    
    Args:
        exchange: ccxt exchange client instance
        symbol (str): Trading pair
    
    Returns:
        dict: Minimum order limits
    """
    
    if not exchange:
        return None
    
    try:
        markets = exchange.load_markets()
        market = markets.get(symbol)
        
        if market:
            return {
                'min_amount': market.get('limits', {}).get('amount', {}).get('min', 0),
                'min_cost': market.get('limits', {}).get('cost', {}).get('min', 0),
                'precision_amount': market.get('precision', {}).get('amount', 8),
                'precision_price': market.get('precision', {}).get('price', 2)
            }
        
        return None
        
    except Exception as e:
        print(f"❌ Error getting order limits: {e}")
        return None


# ============================================
# USAGE EXAMPLES
# ============================================

"""
EXAMPLE 1: Create Exchange Client
----------------------------------
# For testnet (safe testing)
client = create_exchange_client("binance", is_testnet=True)

# For production with API keys
client = create_exchange_client(
    "binance",
    api_key="your_api_key_here",
    api_secret="your_api_secret_here"
)


EXAMPLE 2: Get Account Balances
--------------------------------
client = create_exchange_client("binance", api_key, api_secret)
balances = get_balances(client)

if balances:
    for currency, balance in balances.items():
        print(f"{currency}: {balance['free']} (free), {balance['total']} (total)")


EXAMPLE 3: Place Market Order
------------------------------
client = create_exchange_client("binance", api_key, api_secret, is_testnet=True)

# Buy 0.01 BTC with market order
order = place_market_order(client, "BTC/USDT", "buy", 0.01)

if order:
    print(f"Order executed at ${order['average']}")


EXAMPLE 4: Get Current Price
-----------------------------
client = create_exchange_client("binance")  # No API key needed for public data

ticker = get_ticker(client, "BTC/USDT")
print(f"Bitcoin price: ${ticker['last']}")


EXAMPLE 5: Multiple Exchanges
------------------------------
binance = create_exchange_client("binance")
bybit = create_exchange_client("bybit")
okx = create_exchange_client("okx")

# Get BTC price from all exchanges
for exchange in [binance, bybit, okx]:
    ticker = get_ticker(exchange, "BTC/USDT")
    print(f"{exchange.id}: ${ticker['last']}")


EXAMPLE 6: Check Open Positions (Futures)
------------------------------------------
client = create_exchange_client("bybit", api_key, api_secret)
positions = get_open_positions(client)

for pos in positions:
    pnl_sign = "+" if pos['unrealized_pnl'] >= 0 else ""
    print(f"{pos['symbol']}: {pos['side']} {pos['size']} @ ${pos['entry_price']}")
    print(f"  P/L: {pnl_sign}${pos['unrealized_pnl']}")
"""

# ============================================
# IMPORTANT NOTES
# ============================================

"""
SECURITY BEST PRACTICES:
------------------------
1. Never hardcode API keys in your code
2. Use environment variables: os.getenv('BINANCE_API_KEY')
3. Store keys encrypted in database
4. Use different keys for testnet and production
5. Set IP restrictions on exchange API keys
6. Use read-only API keys if only fetching data
7. Enable 2FA on your exchange account
8. Regularly rotate API keys

RATE LIMITS:
------------
- All exchanges have rate limits (requests per second/minute)
- CCXT automatically handles rate limiting with enableRateLimit=True
- Exceeding limits can result in temporary bans
- Use websockets for real-time data instead of polling

TESTNET VS PRODUCTION:
----------------------
- Always test with testnet first!
- Testnet uses fake money
- Same API, no financial risk
- Not all exchanges support testnet
- Binance, Bybit, OKX have testnet support

SUPPORTED EXCHANGES:
--------------------
This module supports:
- Binance (spot, futures, testnet available)
- Bybit (spot, futures, testnet available)
- OKX (spot, futures, testnet available)
- MEXC (spot, wide altcoin selection)
- BingX (spot, futures, copy trading)

To add more exchanges, just add them to exchange_classes dictionary!

DISCLAIMER:
-----------
This code is for EDUCATIONAL purposes only.
- Paper trading simulation
- University project demonstration
- NOT financial advice
- Real trading involves significant risk
- Always do your own research
- Never trade with money you can't afford to lose
"""

