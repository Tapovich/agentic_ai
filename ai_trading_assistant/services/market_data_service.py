"""
Market Data Service
Fetches external market data from public APIs.

This service provides:
1. Crypto Fear & Greed Index - Shows market sentiment (0-100 scale)
2. Top 100 Cryptocurrencies - Live prices, market caps, volume (CoinMarketCap-style)

APIs Used:
- Alternative.me (Fear & Greed Index) - FREE, no API key needed
- CoinMarketCap (Top coins data) - Requires API key (free tier available)

Educational Purpose:
- Demonstrates API integration
- Shows how to fetch real market data
- Handles errors gracefully
- Beginner-friendly with extensive comments
"""

import requests
import os
from datetime import datetime


# ============================================
# API CONFIGURATION
# ============================================

# Fear & Greed Index API (FREE - No API key needed)
# Alternative.me provides a free API for crypto market sentiment
FEAR_GREED_API_URL = "https://api.alternative.me/fng/"

# CoinMarketCap API (Requires API key - get free at https://coinmarketcap.com/api/)
# Free tier: 10,000 API calls per month (plenty for a university project)
# Import from config.py for centralized configuration
try:
    from config import CMC_API_KEY, CMC_BASE_URL
except ImportError:
    # Fallback if config not available
    CMC_BASE_URL = "https://pro-api.coinmarketcap.com/v1"
    CMC_API_KEY = os.environ.get('CMC_API_KEY', 'YOUR_API_KEY_HERE')

# Timeout for API requests (seconds)
REQUEST_TIMEOUT = 10


# ============================================
# FEAR & GREED INDEX
# ============================================

def get_fear_greed_index():
    """
    Get the Crypto Fear & Greed Index.
    
    What is Fear & Greed Index?
    ============================
    A sentiment indicator for the crypto market (0-100 scale):
    
    - 0-24: Extreme Fear (Good time to buy? Market oversold)
    - 25-49: Fear (Market cautious)
    - 50-74: Greed (Market bullish)
    - 75-100: Extreme Greed (Good time to sell? Market overbought)
    
    How It Works:
    - Analyzes multiple data sources: volatility, market momentum, social media, 
      surveys, Bitcoin dominance, and Google Trends
    - Updates daily
    - Used by traders to gauge market sentiment
    
    Why It Matters:
    - "Be greedy when others are fearful" - Warren Buffett
    - Helps identify market tops (extreme greed) and bottoms (extreme fear)
    - Contrarian indicator for trading decisions
    
    API: Alternative.me (FREE)
    - No API key needed
    - Rate limit: ~100 requests per minute
    - Documentation: https://alternative.me/crypto/fear-and-greed-index/
    
    Returns:
        dict: Fear & Greed data
              {
                  "success": true/false,
                  "value": 42 (0-100),
                  "value_classification": "Fear",
                  "timestamp": "2025-11-13",
                  "error": "..." (if failed)
              }
    
    Example:
        >>> index = get_fear_greed_index()
        >>> print(f"Market sentiment: {index['value_classification']} ({index['value']})")
        Market sentiment: Fear (42)
    """
    
    print(f"\n{'='*70}")
    print(f"FETCHING FEAR & GREED INDEX")
    print(f"{'='*70}")
    
    try:
        # Prepare request parameters
        # limit=1 means we only want the latest value
        params = {
            'limit': 1,
            'format': 'json'
        }
        
        print(f"API: {FEAR_GREED_API_URL}")
        print(f"Params: {params}")
        
        # Send GET request to API
        # timeout=10 means wait max 10 seconds for response
        response = requests.get(
            FEAR_GREED_API_URL, 
            params=params, 
            timeout=REQUEST_TIMEOUT
        )
        
        print(f"Response Status: {response.status_code}")
        
        # Check if request was successful
        # HTTP 200 = OK
        if response.status_code != 200:
            print(f"❌ API returned error status: {response.status_code}")
            return {
                'success': False,
                'error': f'API returned status {response.status_code}'
            }
        
        # Parse JSON response
        data = response.json()
        
        # API returns data in this format:
        # {
        #   "name": "Fear and Greed Index",
        #   "data": [
        #     {
        #       "value": "42",
        #       "value_classification": "Fear",
        #       "timestamp": "1699920000",
        #       "time_until_update": "..."
        #     }
        #   ]
        # }
        
        if 'data' not in data or len(data['data']) == 0:
            print(f"❌ Unexpected API response format")
            return {
                'success': False,
                'error': 'Invalid API response format'
            }
        
        # Extract the latest index data
        latest = data['data'][0]
        
        # Convert timestamp from Unix time to readable format
        timestamp = datetime.fromtimestamp(int(latest['timestamp'])).strftime('%Y-%m-%d %H:%M:%S')
        
        # Parse value (comes as string, convert to int)
        value = int(latest['value'])
        classification = latest['value_classification']
        
        print(f"✅ Fear & Greed Index fetched successfully")
        print(f"   Value: {value}/100")
        print(f"   Classification: {classification}")
        print(f"   Timestamp: {timestamp}")
        print(f"{'='*70}\n")
        
        # Return structured data
        return {
            'success': True,
            'value': value,
            'value_classification': classification,
            'timestamp': timestamp,
            'time_until_update': latest.get('time_until_update', 'Unknown')
        }
        
    except requests.exceptions.Timeout:
        # Request took too long
        print(f"❌ Request timeout - API took longer than {REQUEST_TIMEOUT} seconds")
        return {
            'success': False,
            'error': 'Request timeout - API is slow or unavailable'
        }
        
    except requests.exceptions.ConnectionError:
        # Network problem
        print(f"❌ Connection error - Cannot reach API")
        return {
            'success': False,
            'error': 'Network error - Check internet connection'
        }
        
    except Exception as e:
        # Any other error
        print(f"❌ Unexpected error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


# ============================================
# COINMARKETCAP TOP COINS
# ============================================

def get_top_coins(limit=100, convert='USD'):
    """
    Get top cryptocurrencies by market cap (CoinMarketCap-style).
    
    What This Returns:
    ==================
    A list of the top cryptocurrencies ranked by market capitalization, including:
    - Current price
    - Market cap (total value of all coins)
    - Trading volume (24h)
    - Price changes (1h, 24h, 7d)
    
    Market Cap Explained:
    - Market Cap = Current Price × Circulating Supply
    - Example: Bitcoin at $50,000 with 19M coins = $950B market cap
    - Larger market cap = More established, less volatile
    - Smaller market cap = Higher risk, higher potential returns
    
    API: CoinMarketCap
    - Requires free API key from https://coinmarketcap.com/api/
    - Free tier: 10,000 calls/month (plenty for demo)
    - Sandbox mode available for testing
    
    Args:
        limit (int): Number of coins to return (default: 100, max: 5000)
        convert (str): Target currency (default: "USD", also supports "BTC", "ETH")
    
    Returns:
        dict: Response with coin data
              {
                  "success": true/false,
                  "data": [
                      {
                          "rank": 1,
                          "name": "Bitcoin",
                          "symbol": "BTC",
                          "price": 50000.00,
                          "market_cap": 950000000000,
                          "volume_24h": 25000000000,
                          "percent_change_1h": 0.5,
                          "percent_change_24h": 2.3,
                          "percent_change_7d": -1.2,
                          "circulating_supply": 19000000,
                          "max_supply": 21000000
                      },
                      ...
                  ],
                  "count": 100,
                  "error": "..." (if failed)
              }
    
    Example:
        >>> coins = get_top_coins(limit=10)
        >>> if coins['success']:
        >>>     for coin in coins['data']:
        >>>         print(f"{coin['rank']}. {coin['name']} (${coin['price']:.2f})")
    """
    
    print(f"\n{'='*70}")
    print(f"FETCHING TOP {limit} CRYPTOCURRENCIES")
    print(f"{'='*70}")
    
    # ========================================
    # STEP 1: Check API Key
    # ========================================
    
    if not CMC_API_KEY or CMC_API_KEY == 'YOUR_API_KEY_HERE':
        print(f"⚠️ CoinMarketCap API key not configured!")
        print(f"   To use this feature:")
        print(f"   1. Get free API key at https://coinmarketcap.com/api/")
        print(f"   2. Set environment variable: export CMC_API_KEY='your-key-here'")
        print(f"   3. Or update config.py with your key")
        print(f"\n   Returning demo data for now...")
        
        # Return demo/placeholder data for development
        return {
            'success': False,
            'error': 'API key not configured. Get free key at https://coinmarketcap.com/api/',
            'demo_mode': True,
            'data': _get_demo_coins_data(limit)
        }
    
    # ========================================
    # STEP 2: Prepare API Request
    # ========================================
    
    try:
        # CoinMarketCap API endpoint for latest listings
        url = f"{CMC_BASE_URL}/cryptocurrency/listings/latest"
        
        # Request headers
        # X-CMC_PRO_API_KEY is required for authentication
        headers = {
            'X-CMC_PRO_API_KEY': CMC_API_KEY,
            'Accept': 'application/json'
        }
        
        # Request parameters
        params = {
            'limit': limit,          # How many coins to return
            'convert': convert,      # Target currency (USD, BTC, ETH)
            'sort': 'market_cap',    # Sort by market cap (largest first)
            'sort_dir': 'desc'       # Descending order (biggest to smallest)
        }
        
        print(f"API: {url}")
        print(f"Limit: {limit} coins")
        print(f"Convert: {convert}")
        print(f"Sending request...")
        
        # ========================================
        # STEP 3: Send Request
        # ========================================
        
        response = requests.get(
            url, 
            headers=headers, 
            params=params, 
            timeout=REQUEST_TIMEOUT
        )
        
        print(f"Response Status: {response.status_code}")
        
        # Check for errors
        if response.status_code == 401:
            # Unauthorized - API key invalid
            print(f"❌ Invalid API key")
            return {
                'success': False,
                'error': 'Invalid CoinMarketCap API key'
            }
        
        elif response.status_code == 429:
            # Too many requests - rate limit exceeded
            print(f"❌ Rate limit exceeded")
            return {
                'success': False,
                'error': 'API rate limit exceeded. Try again later.'
            }
        
        elif response.status_code != 200:
            # Other error
            print(f"❌ API error: {response.status_code}")
            return {
                'success': False,
                'error': f'API returned status {response.status_code}'
            }
        
        # ========================================
        # STEP 4: Parse Response
        # ========================================
        
        data = response.json()
        
        # CoinMarketCap response structure:
        # {
        #   "status": {...},
        #   "data": [
        #     {
        #       "id": 1,
        #       "name": "Bitcoin",
        #       "symbol": "BTC",
        #       "cmc_rank": 1,
        #       "quote": {
        #         "USD": {
        #           "price": 50000,
        #           "market_cap": 950000000000,
        #           "volume_24h": 25000000000,
        #           "percent_change_1h": 0.5,
        #           "percent_change_24h": 2.3,
        #           "percent_change_7d": -1.2
        #         }
        #       },
        #       ...
        #     },
        #     ...
        #   ]
        # }
        
        if 'data' not in data:
            print(f"❌ Invalid API response format")
            return {
                'success': False,
                'error': 'Invalid API response format'
            }
        
        # ========================================
        # STEP 5: Extract and Format Coin Data
        # ========================================
        
        coins = []
        
        for coin in data['data']:
            # Extract quote data for target currency (usually USD)
            if convert not in coin.get('quote', {}):
                continue
            
            quote = coin['quote'][convert]
            
            # Build simplified coin object
            coin_data = {
                'rank': coin.get('cmc_rank', 0),
                'name': coin.get('name', 'Unknown'),
                'symbol': coin.get('symbol', 'N/A'),
                'price': round(quote.get('price', 0), 2),
                'market_cap': round(quote.get('market_cap', 0), 2),
                'volume_24h': round(quote.get('volume_24h', 0), 2),
                'percent_change_1h': round(quote.get('percent_change_1h', 0), 2),
                'percent_change_24h': round(quote.get('percent_change_24h', 0), 2),
                'percent_change_7d': round(quote.get('percent_change_7d', 0), 2),
                'circulating_supply': round(coin.get('circulating_supply', 0), 2),
                'max_supply': round(coin.get('max_supply', 0), 2) if coin.get('max_supply') else None,
                'last_updated': coin.get('last_updated', '')
            }
            
            coins.append(coin_data)
        
        print(f"✅ Fetched {len(coins)} coins successfully")
        print(f"   Top 3:")
        for i, coin in enumerate(coins[:3]):
            print(f"   {i+1}. {coin['name']} (${coin['price']:,.2f})")
        print(f"{'='*70}\n")
        
        # ========================================
        # STEP 6: Return Formatted Data
        # ========================================
        
        return {
            'success': True,
            'data': coins,
            'count': len(coins),
            'convert': convert
        }
        
    except requests.exceptions.Timeout:
        print(f"❌ Request timeout")
        return {
            'success': False,
            'error': 'Request timeout - API is slow or unavailable'
        }
        
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection error")
        return {
            'success': False,
            'error': 'Network error - Check internet connection'
        }
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }


# ============================================
# DEMO DATA (for when API key not configured)
# ============================================

def _get_demo_coins_data(limit=100):
    """
    Returns demo/placeholder data when API key is not configured.
    
    This allows the app to run and be demonstrated without a real API key.
    Useful for university projects and development.
    
    Note: This is static demo data, not real market data!
    """
    
    demo_coins = [
        {'rank': 1, 'name': 'Bitcoin', 'symbol': 'BTC', 'price': 98500.00, 'market_cap': 1950000000000, 'volume_24h': 45000000000, 'percent_change_1h': 0.5, 'percent_change_24h': 2.3, 'percent_change_7d': -1.2},
        {'rank': 2, 'name': 'Ethereum', 'symbol': 'ETH', 'price': 3800.00, 'market_cap': 450000000000, 'volume_24h': 20000000000, 'percent_change_1h': 0.3, 'percent_change_24h': 1.8, 'percent_change_7d': 3.5},
        {'rank': 3, 'name': 'Binance Coin', 'symbol': 'BNB', 'price': 650.00, 'market_cap': 95000000000, 'volume_24h': 2000000000, 'percent_change_1h': -0.2, 'percent_change_24h': 0.9, 'percent_change_7d': 5.2},
        {'rank': 4, 'name': 'Solana', 'symbol': 'SOL', 'price': 230.00, 'market_cap': 75000000000, 'volume_24h': 3500000000, 'percent_change_1h': 1.2, 'percent_change_24h': 5.6, 'percent_change_7d': 12.3},
        {'rank': 5, 'name': 'XRP', 'symbol': 'XRP', 'price': 0.62, 'market_cap': 35000000000, 'volume_24h': 1500000000, 'percent_change_1h': 0.1, 'percent_change_24h': -0.5, 'percent_change_7d': 2.1},
    ]
    
    # Return only up to 'limit' coins
    return demo_coins[:min(limit, len(demo_coins))]


# ============================================
# LIVE PRICE QUOTES
# ============================================

def get_live_prices(symbols, convert='USD'):
    """
    Get live prices for specific cryptocurrency symbols.
    
    Perfect for real-time price updates in UI.
    
    Args:
        symbols (list or str): List of symbols like ['BTC', 'ETH', 'BNB'] or single 'BTC'
        convert (str): Target currency (default: 'USD')
    
    Returns:
        dict: {
            'success': True/False,
            'prices': {
                'BTC': {'price': 98500.00, 'percent_change_24h': 2.3, 'last_updated': '...'},
                'ETH': {'price': 3800.00, 'percent_change_24h': 1.8, 'last_updated': '...'},
                ...
            },
            'timestamp': '2025-11-15 12:00:00'
        }
    """
    
    # Convert single symbol to list
    if isinstance(symbols, str):
        symbols = [symbols]
    
    # Check API key
    if not CMC_API_KEY or CMC_API_KEY == 'YOUR_API_KEY_HERE':
        # Return demo data
        demo_prices = {
            'BTC': {'price': 98500.00, 'percent_change_24h': 2.3, 'percent_change_1h': 0.5},
            'ETH': {'price': 3800.00, 'percent_change_24h': 1.8, 'percent_change_1h': 0.3},
            'BNB': {'price': 650.00, 'percent_change_24h': 0.9, 'percent_change_1h': -0.2},
            'SOL': {'price': 230.00, 'percent_change_24h': 5.6, 'percent_change_1h': 1.2},
            'XRP': {'price': 0.62, 'percent_change_24h': -0.5, 'percent_change_1h': 0.1},
        }
        
        result_prices = {sym: demo_prices.get(sym, {'price': 0, 'percent_change_24h': 0, 'percent_change_1h': 0}) 
                        for sym in symbols}
        
        return {
            'success': True,
            'demo_mode': True,
            'prices': result_prices,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    try:
        url = f"{CMC_BASE_URL}/cryptocurrency/quotes/latest"
        
        headers = {
            'X-CMC_PRO_API_KEY': CMC_API_KEY,
            'Accept': 'application/json'
        }
        
        params = {
            'symbol': ','.join(symbols),  # Comma-separated symbols
            'convert': convert
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
        
        if response.status_code != 200:
            return {'success': False, 'error': f'API returned status {response.status_code}'}
        
        data = response.json()
        
        if 'data' not in data:
            return {'success': False, 'error': 'Invalid API response'}
        
        # Extract prices
        prices = {}
        for symbol in symbols:
            if symbol in data['data']:
                quote = data['data'][symbol]['quote'][convert]
                prices[symbol] = {
                    'price': round(quote['price'], 2),
                    'percent_change_1h': round(quote.get('percent_change_1h', 0), 2),
                    'percent_change_24h': round(quote.get('percent_change_24h', 0), 2),
                    'percent_change_7d': round(quote.get('percent_change_7d', 0), 2),
                    'volume_24h': round(quote.get('volume_24h', 0), 2),
                    'market_cap': round(quote.get('market_cap', 0), 2),
                    'last_updated': quote.get('last_updated', '')
                }
        
        return {
            'success': True,
            'prices': prices,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
    except Exception as e:
        print(f"Error fetching live prices: {e}")
        return {'success': False, 'error': str(e)}


# ============================================
# DETAILED TOKEN INFORMATION (For Hover Tooltips)
# ============================================

def get_token_details(symbol, convert='USD'):
    """
    Get detailed information about a specific cryptocurrency.
    
    Perfect for hover tooltips and detailed views.
    
    Returns comprehensive data including:
    - Price and market cap
    - Trading volume
    - Price changes (1h, 24h, 7d, 30d)
    - Circulating/total/max supply
    - All-time high/low
    - Description and links
    
    Args:
        symbol (str): Cryptocurrency symbol (e.g., 'BTC', 'ETH')
        convert (str): Target currency (default: 'USD')
    
    Returns:
        dict: Detailed token information for display
    """
    
    # Check API key
    if not CMC_API_KEY or CMC_API_KEY == 'YOUR_API_KEY_HERE':
        # Return demo data
        demo_details = {
            'BTC': {
                'name': 'Bitcoin',
                'symbol': 'BTC',
                'price': 98500.00,
                'market_cap': 1950000000000,
                'market_cap_rank': 1,
                'volume_24h': 45000000000,
                'percent_change_1h': 0.5,
                'percent_change_24h': 2.3,
                'percent_change_7d': -1.2,
                'percent_change_30d': 8.5,
                'circulating_supply': 19000000,
                'total_supply': 19000000,
                'max_supply': 21000000,
                'ath': 102000.00,
                'ath_date': '2024-12-15',
                'atl': 65.00,
                'atl_date': '2013-07-05',
                'description': 'Bitcoin is a decentralized digital currency without a central bank or administrator. It can be sent from user to user on the peer-to-peer bitcoin network.',
                'category': 'currency',
                'tags': ['mineable', 'pow', 'sha-256']
            },
            'ETH': {
                'name': 'Ethereum',
                'symbol': 'ETH',
                'price': 3800.00,
                'market_cap': 450000000000,
                'market_cap_rank': 2,
                'volume_24h': 20000000000,
                'percent_change_1h': 0.3,
                'percent_change_24h': 1.8,
                'percent_change_7d': 3.5,
                'percent_change_30d': 12.3,
                'circulating_supply': 120000000,
                'total_supply': 120000000,
                'max_supply': None,
                'ath': 4800.00,
                'ath_date': '2021-11-10',
                'atl': 0.43,
                'atl_date': '2015-10-20',
                'description': 'Ethereum is a decentralized platform for applications that run exactly as programmed without any possibility of fraud or third party interference.',
                'category': 'smart-contract-platform',
                'tags': ['smart-contracts', 'ethereum-ecosystem', 'pos']
            }
        }
        
        details = demo_details.get(symbol, {
            'name': symbol,
            'symbol': symbol,
            'price': 0,
            'description': 'Demo mode - API key not configured'
        })
        
        return {
            'success': True,
            'demo_mode': True,
            'data': details
        }
    
    try:
        # First, get quote data
        url = f"{CMC_BASE_URL}/cryptocurrency/quotes/latest"
        
        headers = {
            'X-CMC_PRO_API_KEY': CMC_API_KEY,
            'Accept': 'application/json'
        }
        
        params = {
            'symbol': symbol,
            'convert': convert,
            'aux': 'urls,logo,description,tags,platform,date_added,notice'
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
        
        if response.status_code != 200:
            return {'success': False, 'error': f'API returned status {response.status_code}'}
        
        data = response.json()
        
        if 'data' not in data or symbol not in data['data']:
            return {'success': False, 'error': 'Token not found'}
        
        coin = data['data'][symbol]
        quote = coin['quote'][convert]
        
        # Build detailed response
        details = {
            'name': coin.get('name', symbol),
            'symbol': coin.get('symbol', symbol),
            'slug': coin.get('slug', ''),
            'logo': f"https://s2.coinmarketcap.com/static/img/coins/64x64/{coin.get('id', 1)}.png",
            'category': coin.get('category', ''),
            'description': coin.get('description', ''),
            'tags': coin.get('tags', []),
            
            # Price data
            'price': round(quote.get('price', 0), 2),
            'market_cap': round(quote.get('market_cap', 0), 2),
            'market_cap_rank': coin.get('cmc_rank', 0),
            'volume_24h': round(quote.get('volume_24h', 0), 2),
            'volume_change_24h': round(quote.get('volume_change_24h', 0), 2),
            
            # Price changes
            'percent_change_1h': round(quote.get('percent_change_1h', 0), 2),
            'percent_change_24h': round(quote.get('percent_change_24h', 0), 2),
            'percent_change_7d': round(quote.get('percent_change_7d', 0), 2),
            'percent_change_30d': round(quote.get('percent_change_30d', 0), 2),
            'percent_change_60d': round(quote.get('percent_change_60d', 0), 2),
            'percent_change_90d': round(quote.get('percent_change_90d', 0), 2),
            
            # Supply data
            'circulating_supply': round(coin.get('circulating_supply', 0), 2),
            'total_supply': round(coin.get('total_supply', 0), 2) if coin.get('total_supply') else None,
            'max_supply': round(coin.get('max_supply', 0), 2) if coin.get('max_supply') else None,
            
            # Market dominance
            'market_cap_dominance': round(quote.get('market_cap_dominance', 0), 2),
            
            # URLs
            'website': coin.get('urls', {}).get('website', []),
            'explorer': coin.get('urls', {}).get('explorer', []),
            'technical_doc': coin.get('urls', {}).get('technical_doc', []),
            'twitter': coin.get('urls', {}).get('twitter', []),
            'reddit': coin.get('urls', {}).get('reddit', []),
            
            # Dates
            'date_added': coin.get('date_added', ''),
            'last_updated': quote.get('last_updated', '')
        }
        
        return {
            'success': True,
            'data': details
        }
        
    except Exception as e:
        print(f"Error fetching token details for {symbol}: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}


# ============================================
# EDUCATIONAL NOTES
# ============================================

"""
HOW TO USE THIS SERVICE:
========================

1. Fear & Greed Index:
   -------------------
   from services import market_data_service
   
   index = market_data_service.get_fear_greed_index()
   
   if index['success']:
       print(f"Market is in {index['value_classification']} mode")
       print(f"Index value: {index['value']}/100")
   else:
       print(f"Error: {index['error']}")


2. Top Coins:
   ----------
   coins = market_data_service.get_top_coins(limit=10)
   
   if coins['success']:
       for coin in coins['data']:
           print(f"{coin['rank']}. {coin['name']}: ${coin['price']}")
   else:
       print(f"Error: {coins['error']}")


API KEY SETUP:
=============

For CoinMarketCap:
1. Go to https://coinmarketcap.com/api/
2. Sign up for free account
3. Get your API key (free tier: 10,000 calls/month)
4. Set environment variable:
   
   On Mac/Linux:
   export CMC_API_KEY="your-api-key-here"
   
   On Windows:
   set CMC_API_KEY=your-api-key-here
   
   Or add to your .env file:
   CMC_API_KEY=your-api-key-here

5. Restart your Flask server


RATE LIMITS:
===========

Fear & Greed (Alternative.me):
- Free API
- ~100 requests per minute
- No API key needed

CoinMarketCap (Free Tier):
- 10,000 calls per month
- ~333 calls per day
- 1 call = 1 credit
- Sufficient for demo/university project


SECURITY BEST PRACTICES:
========================

1. Never commit API keys to Git
2. Use environment variables
3. Add .env to .gitignore
4. Use different keys for dev/prod
5. Rotate keys regularly


FOR UNIVERSITY PROJECTS:
========================

If you can't get a CoinMarketCap API key:
- The service falls back to demo data
- You can demonstrate the architecture
- Explain: "In production, this would fetch real data from CoinMarketCap"
- Professor will understand it's a demo/educational project
"""

