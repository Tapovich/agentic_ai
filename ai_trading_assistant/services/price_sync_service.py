"""
Price Synchronization Service
Fetches REAL market data from exchanges and stores in database.

PURPOSE:
========
This service REPLACES all dummy/static price data with REAL market candles.

Before: price_history had hardcoded/CSV data
After: price_history has REAL candles from Binance/Bybit/OKX via CCXT

Why This Matters:
-----------------
1. Technical Indicators: SMA and RSI now calculated from REAL market data
2. AI Model: Trains on REAL historical prices
3. Trading Decisions: Based on REAL market conditions
4. Accuracy: Everything reflects actual market

How It Works:
------------
1. Click "Sync Latest Prices" button
2. Fetches 200 recent candles from Binance
3. Stores in price_history table
4. Technical indicators auto-update with real data
5. AI predictions based on real market

Single Source of Truth:
----------------------
All price data flows through this pipeline:
Exchange (via CCXT) → This Service → Database → Platform Features
"""

import ccxt
from datetime import datetime
from models import db


def sync_price_history_for_symbol(symbol, timeframe="1h", limit=200, exchange_name="binance"):
    """
    Sync real OHLCV data from exchange into price_history table.
    
    REPLACES DUMMY DATA WITH REAL MARKET CANDLES!
    
    What This Does:
    ===============
    1. Fetches recent candles from exchange (Binance/Bybit/OKX)
    2. Checks which candles are already in database
    3. Inserts new candles (avoids duplicates)
    4. Updates database with real market data
    
    Why This is Important:
    =====================
    - Technical indicators (SMA, RSI) need real data
    - AI model trains on real market conditions
    - Trading decisions based on actual prices
    - No more hardcoded/CSV data!
    
    Args:
        symbol (str): Symbol to sync (e.g., "BTCUSDT")
        timeframe (str): Candle interval ("1m", "5m", "15m", "1h", "4h", "1d")
        limit (int): Number of recent candles to fetch (default: 200)
        exchange_name (str): Which exchange to use (default: "binance")
    
    Returns:
        dict: Sync result with statistics
              {
                  "success": true,
                  "symbol": "BTCUSDT",
                  "fetched": 200,
                  "inserted": 150,
                  "duplicates": 50,
                  "timeframe": "1h"
              }
    
    Example:
        # Sync 200 hourly Bitcoin candles from Binance
        result = sync_price_history_for_symbol("BTCUSDT", timeframe="1h", limit=200)
        
        print(f"Fetched: {result['fetched']} candles")
        print(f"Inserted: {result['inserted']} new candles")
        print(f"Duplicates skipped: {result['duplicates']}")
    
    Timeframe Guide:
        - "1m": 1 minute (for day trading)
        - "15m": 15 minutes (for swing trading)
        - "1h": 1 hour (for indicators, recommended)
        - "4h": 4 hours (for position trading)
        - "1d": Daily (for long-term analysis)
    """
    
    print(f"\n{'='*70}")
    print(f"SYNCING PRICE HISTORY")
    print(f"{'='*70}")
    print(f"Symbol: {symbol}")
    print(f"Exchange: {exchange_name}")
    print(f"Timeframe: {timeframe}")
    print(f"Limit: {limit}")
    print(f"{'='*70}\n")
    
    try:
        # Normalize symbol
        symbol_normalized = normalize_symbol(symbol)
        symbol_db = symbol.replace('/', '')  # For database storage
        
        # ========================================
        # Step 1: Fetch Real Data from Exchange
        # ========================================
        
        print(f"[1] Fetching real market data from {exchange_name}...")
        
        # Get exchange client
        client = get_exchange_client_for_prices(exchange_name)
        
        if not client:
            return {
                'success': False,
                'error': f'Failed to create {exchange_name} client'
            }
        
        # Fetch OHLCV candles from exchange
        ohlcv_data = client.fetch_ohlcv(symbol_normalized, timeframe=timeframe, limit=limit)
        
        print(f"✅ Fetched {len(ohlcv_data)} candles from {exchange_name}")
        
        if not ohlcv_data:
            return {
                'success': False,
                'error': 'No data returned from exchange'
            }
        
        # ========================================
        # Step 2: Check Existing Data in Database
        # ========================================
        
        print(f"\n[2] Checking for existing data in database...")
        
        # Get existing timestamps for this symbol
        query = """
            SELECT timestamp FROM price_history
            WHERE symbol = ?
        """
        
        existing = db.fetch_all(query, (symbol_db,))
        existing_timestamps = set()
        
        if existing:
            for row in existing:
                existing_timestamps.add(row['timestamp'])
        
        print(f"   Found {len(existing_timestamps)} existing candles in database")
        
        # ========================================
        # Step 3: Insert New Candles
        # ========================================
        
        print(f"\n[3] Inserting new candles...")
        
        inserted_count = 0
        duplicate_count = 0
        
        for candle in ohlcv_data:
            # CCXT OHLCV format: [timestamp_ms, open, high, low, close, volume]
            timestamp_ms = candle[0]
            timestamp_str = datetime.fromtimestamp(timestamp_ms / 1000).strftime('%Y-%m-%d %H:%M:%S')
            
            open_price = float(candle[1])
            high_price = float(candle[2])
            low_price = float(candle[3])
            close_price = float(candle[4])
            volume = float(candle[5]) if candle[5] else 0
            
            # Check if this timestamp already exists
            if timestamp_str in existing_timestamps:
                duplicate_count += 1
                continue
            
            # Insert new candle
            query = """
                INSERT INTO price_history 
                (symbol, timestamp, open_price, high_price, low_price, close_price, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            
            result = db.execute_query(query, (
                symbol_db,
                timestamp_str,
                open_price,
                high_price,
                low_price,
                close_price,
                volume
            ))
            
            if result:
                inserted_count += 1
        
        # ========================================
        # Step 4: Report Results
        # ========================================
        
        print(f"\n✅ Sync Complete!")
        print(f"   Fetched from exchange: {len(ohlcv_data)}")
        print(f"   Inserted new candles: {inserted_count}")
        print(f"   Duplicates skipped: {duplicate_count}")
        
        # Get latest price for display
        latest_candle = ohlcv_data[-1]
        latest_price = float(latest_candle[4])
        
        print(f"   Latest {symbol} price: ${latest_price:,.2f}")
        print(f"{'='*70}\n")
        
        return {
            'success': True,
            'symbol': symbol,
            'symbol_db': symbol_db,
            'exchange': exchange_name,
            'timeframe': timeframe,
            'fetched': len(ohlcv_data),
            'inserted': inserted_count,
            'duplicates': duplicate_count,
            'latest_price': latest_price,
            'message': f'Synced {inserted_count} new candles for {symbol}'
        }
        
    except Exception as e:
        print(f"❌ Error syncing price history: {e}")
        return {
            'success': False,
            'error': str(e),
            'message': 'Failed to sync prices from exchange'
        }


# ============================================
# HELPER FUNCTIONS
# ============================================

def get_exchange_client_for_prices(exchange_name="binance"):
    """
    Get ccxt exchange client for public market data.
    No API key required - public data only!
    
    Args:
        exchange_name (str): Exchange to use
    
    Returns:
        ccxt.Exchange: Exchange client
    """
    
    try:
        exchanges = {
            'binance': ccxt.binance,
            'bybit': ccxt.bybit,
            'okx': ccxt.okx,
            'mexc': ccxt.mexc,
            'bingx': ccxt.bingx
        }
        
        exchange_name = exchange_name.lower()
        ExchangeClass = exchanges.get(exchange_name, ccxt.binance)
        
        return ExchangeClass({
            'enableRateLimit': True  # Prevents rate limit bans
        })
        
    except Exception as e:
        print(f"❌ Error creating exchange client: {e}")
        return None


def normalize_symbol(symbol_str):
    """
    Normalize symbol to ccxt format.
    
    BTCUSDT → BTC/USDT
    BTC/USDT → BTC/USDT
    """
    
    if not symbol_str:
        return "BTC/USDT"
    
    symbol_str = symbol_str.strip().upper()
    
    # Already normalized
    if '/' in symbol_str:
        return symbol_str
    
    # Add slash
    if symbol_str.endswith('USDT'):
        base = symbol_str[:-4]
        return f"{base}/USDT"
    
    return f"{symbol_str}/USDT"


def sync_multiple_symbols(symbols, timeframe="1h", limit=200):
    """
    Sync price history for multiple symbols.
    
    Useful for:
    - Initial database population
    - Bulk updates
    - Multiple asset tracking
    
    Args:
        symbols (list): List of symbols to sync
        timeframe (str): Candle interval
        limit (int): Candles per symbol
    
    Returns:
        dict: Results for all symbols
    
    Example:
        results = sync_multiple_symbols(["BTCUSDT", "ETHUSDT", "BNBUSDT"])
        
        for symbol, result in results.items():
            if result['success']:
                print(f"{symbol}: {result['inserted']} candles synced")
    """
    
    results = {}
    
    for symbol in symbols:
        print(f"\nSyncing {symbol}...")
        result = sync_price_history_for_symbol(symbol, timeframe, limit)
        results[symbol] = result
    
    return results


# ============================================
# EDUCATIONAL NOTES
# ============================================

"""
WHAT THIS SERVICE DOES:
=======================

Replaces: Static/dummy data
With: Real market data from exchanges

Impact on Platform:
------------------

1. Technical Indicators
   Before: Calculated from dummy data
   After: Calculated from REAL Bitcoin prices!
   Result: Accurate SMA, RSI values

2. AI Model
   Before: Trained on CSV sample data
   After: Can train on real market history
   Result: Better predictions

3. Trading Decisions
   Before: Based on hardcoded $45,000
   After: Based on real $100,963 market price
   Result: Realistic simulations

4. Charts & Visualizations
   Before: Static demo data
   After: Real historical candles
   Result: Professional display

How to Use:
----------

Initial Setup:
```python
# Sync major cryptocurrencies
sync_multiple_symbols(["BTCUSDT", "ETHUSDT", "BNBUSDT"])
```

Regular Updates (Production):
```python
# Run every hour via cron
sync_price_history_for_symbol("BTCUSDT", limit=60)
```

Manual Update (Demo):
- Click "Sync Latest Prices" button on dashboard
- Fetches fresh data from Binance
- Updates database immediately

Benefits:
--------

1. Real Data: No more dummy prices
2. Up-to-Date: Always current market data
3. Accurate: Technical indicators reflect reality
4. Professional: Like real trading platforms
5. Educational: Shows real-world data flow

Limitations:
-----------

1. API Rate Limits: Can't sync too frequently
2. Exchange Uptime: Depends on exchange availability
3. Network: Requires internet connection
4. Storage: More data = bigger database

For University Project:
----------------------

This demonstrates:
- Real-world data integration
- API usage
- Database synchronization
- Professional architecture
- Production-ready approach

Perfect for explaining:
"Our platform uses REAL market data from Binance, 
synchronized into our database for analysis and trading."
"""

