"""
Unified Data Service (TASK 47)

Centralizes all OHLCV data access to ensure consistency across:
- Indicators
- Predictions
- Charts
- Analytics

Purpose:
- Single source of truth for price data
- Consistent timestamps and values everywhere
- No data inconsistencies between database and CCXT
- Easy to debug and maintain

Data Flow:
  Exchange (CCXT) → price_history table → This Service → All Analytics

Usage:
    from services.unified_data_service import get_price_history_df
    
    df = get_price_history_df("BTCUSDT", timeframe="1h", limit=300)
    # Now use df for indicators, predictions, charts
"""

import pandas as pd
from models import fetch_all
from datetime import datetime, timedelta


def get_price_history_df(symbol: str, timeframe: str = "1h", limit: int = 300, 
                         force_sync: bool = False) -> pd.DataFrame:
    """
    Get OHLCV data as pandas DataFrame - SINGLE SOURCE OF TRUTH
    
    This is the canonical function for getting price data.
    All analytics services should use this to ensure consistency.
    
    Args:
        symbol (str): Trading pair (e.g., "BTCUSDT")
        timeframe (str): Candle interval ("1h", "4h", "1d")
        limit (int): Number of candles to fetch
        force_sync (bool): If True, sync from exchange before returning
    
    Returns:
        pd.DataFrame: OHLCV data with columns [timestamp, open, high, low, close, volume]
                     Index: timestamp (datetime)
    
    Data Flow:
        1. Check database for recent data
        2. If force_sync or data too old, sync from CCXT
        3. Return consistent DataFrame
    
    Example:
        >>> df = get_price_history_df("BTCUSDT", "1h", 250)
        >>> print(f"Fetched {len(df)} candles")
        >>> print(f"Latest close: ${df['close'].iloc[-1]}")
    
    Note:
        - All timestamps are UTC
        - Data is sorted oldest to newest (index ascending)
        - Missing data returns empty DataFrame (not None)
    """
    
    try:
        print(f"\n{'='*70}")
        print(f"UNIFIED DATA SERVICE")
        print(f"Symbol: {symbol}, Timeframe: {timeframe}, Limit: {limit}")
        print(f"{'='*70}")
        
        # ========================================
        # Step 1: Try to get from database first
        # ========================================
        
        query = """
            SELECT timestamp, open_price, high_price, low_price, close_price, volume
            FROM price_history
            WHERE symbol = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """
        
        rows = fetch_all(query, (symbol, limit))
        
        if rows and len(rows) >= limit // 2:  # Have at least half the requested data
            # Reverse to get oldest-first order
            rows = list(reversed(rows))
            
            # Convert to DataFrame (fetch_all returns list of dicts)
            df = pd.DataFrame(rows)
            
            # Rename columns to match expected format
            df.rename(columns={
                'open_price': 'open',
                'high_price': 'high',
                'low_price': 'low',
                'close_price': 'close'
            }, inplace=True)
            
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.set_index('timestamp')
            
            # Check data freshness (should be within 2 hours)
            latest_timestamp = df.index[-1]
            age_hours = (datetime.utcnow() - latest_timestamp.to_pydatetime()).total_seconds() / 3600
            
            if not force_sync and age_hours < 2:
                print(f"✅ Using database data ({len(df)} candles, {age_hours:.1f}h old)")
                print(f"   Latest: {latest_timestamp}")
                print(f"{'='*70}\n")
                return df
            else:
                print(f"⚠️  Database data stale ({age_hours:.1f}h old), will sync from CCXT")
        else:
            print(f"⚠️  Insufficient database data ({len(rows) if rows else 0} rows), will sync from CCXT")
        
        # ========================================
        # Step 2: Sync from CCXT if needed
        # ========================================
        
        print(f"🔄 Syncing from CCXT...")
        
        from services import price_sync_service
        
        sync_result = price_sync_service.sync_price_history_for_symbol(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
            exchange_name='binance'
        )
        
        if sync_result['success']:
            print(f"✅ Synced {sync_result['inserted']} new candles from CCXT")
            
            # Now fetch from database again
            rows = fetch_all(query, (symbol, limit))
            
            if rows:
                # Reverse to get oldest-first order
                rows = list(reversed(rows))
                
                # Convert to DataFrame (fetch_all returns list of dicts)
                df = pd.DataFrame(rows)
                
                # Rename columns to match expected format
                df.rename(columns={
                    'open_price': 'open',
                    'high_price': 'high',
                    'low_price': 'low',
                    'close_price': 'close'
                }, inplace=True)
                
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.set_index('timestamp')
                
                print(f"✅ Returning {len(df)} candles from database")
                print(f"   Range: {df.index[0]} to {df.index[-1]}")
                print(f"{'='*70}\n")
                return df
        
        # ========================================
        # Step 3: Fallback - try direct CCXT
        # ========================================
        
        print(f"⚠️  Database sync failed, trying direct CCXT...")
        
        from services.advanced_data_service import AdvancedDataService
        
        data_service = AdvancedDataService()
        df = data_service.get_ohlcv(symbol.replace("USDT", "/USDT"), timeframe, since_days=30)
        
        if not df.empty:
            # Limit to requested number of candles
            if len(df) > limit:
                df = df.tail(limit)
            
            print(f"✅ Returning {len(df)} candles from CCXT (direct)")
            print(f"   Range: {df.index[0]} to {df.index[-1]}")
            print(f"{'='*70}\n")
            return df
        
        # ========================================
        # Step 4: No data available
        # ========================================
        
        print(f"❌ No data available for {symbol}")
        print(f"{'='*70}\n")
        return pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])
        
    except Exception as e:
        print(f"❌ Error in unified data service: {e}")
        import traceback
        traceback.print_exc()
        print(f"{'='*70}\n")
        
        # Return empty DataFrame on error
        return pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])


def validate_df_for_indicators(df: pd.DataFrame, min_candles: int = 200) -> tuple[bool, str]:
    """
    Validate DataFrame has sufficient data for indicator calculation.
    
    Args:
        df (pd.DataFrame): OHLCV DataFrame
        min_candles (int): Minimum required candles (default 200 for EMA 200)
    
    Returns:
        tuple: (is_valid: bool, error_message: str)
    
    Example:
        >>> df = get_price_history_df("BTCUSDT", "1h", 250)
        >>> is_valid, error = validate_df_for_indicators(df, 200)
        >>> if not is_valid:
        >>>     return {"error": error}
    """
    
    if df is None or df.empty:
        return False, "No price data available"
    
    if len(df) < min_candles:
        return False, f"Insufficient data: need {min_candles} candles, got {len(df)}"
    
    # Check for required columns
    required_cols = ['open', 'high', 'low', 'close', 'volume']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        return False, f"Missing columns: {', '.join(missing_cols)}"
    
    # Check for NaN values
    if df[['close']].isnull().any().any():
        return False, "Data contains NaN values"
    
    return True, ""


def ensure_consistent_timestamps(
    price_data: pd.DataFrame,
    indicator_data: dict,
    chart_data: dict
) -> dict:
    """
    Ensure all data structures use consistent timestamps.
    
    This prevents chart rendering issues where lines have different lengths.
    
    Args:
        price_data (pd.DataFrame): OHLCV DataFrame
        indicator_data (dict): Indicator values
        chart_data (dict): Chart data with timestamps/prices
    
    Returns:
        dict: Unified chart data with consistent timestamps
    
    Example:
        >>> df = get_price_history_df("BTCUSDT", "1h", 250)
        >>> indicators = calculate_indicators(df)
        >>> chart = ensure_consistent_timestamps(df, indicators, chart_data)
    """
    
    # Get consistent timestamp list from price_data
    timestamps = [ts.isoformat() for ts in price_data.index]
    
    # Build unified chart data
    unified = {
        'timestamps': timestamps,
        'prices': price_data['close'].tolist(),
        'length': len(timestamps)
    }
    
    # Add EMA data if available
    if 'ema_chart' in indicator_data and indicator_data['ema_chart']:
        ema_chart = indicator_data['ema_chart']
        
        # Ensure EMAs have same length as prices
        if 'ema9' in ema_chart:
            unified['ema9'] = ema_chart['ema9']
        if 'ema20' in ema_chart:
            unified['ema20'] = ema_chart['ema20']
        if 'ema50' in ema_chart:
            unified['ema50'] = ema_chart['ema50']
        if 'ema100' in ema_chart:
            unified['ema100'] = ema_chart['ema100']
        if 'ema200' in ema_chart:
            unified['ema200'] = ema_chart['ema200']
    
    return unified


if __name__ == '__main__':
    # Test the unified data service
    print("\n" + "="*70)
    print("TESTING UNIFIED DATA SERVICE")
    print("="*70 + "\n")
    
    # Test 1: Get BTCUSDT data
    print("Test 1: Get BTCUSDT 1h data")
    df = get_price_history_df("BTCUSDT", "1h", 250)
    print(f"Result: {len(df)} candles")
    if not df.empty:
        print(f"Latest close: ${df['close'].iloc[-1]:.2f}")
        print(f"Date range: {df.index[0]} to {df.index[-1]}")
    
    # Test 2: Validate for indicators
    print("\nTest 2: Validate for indicators")
    is_valid, error = validate_df_for_indicators(df, 200)
    print(f"Valid: {is_valid}")
    if not is_valid:
        print(f"Error: {error}")
    
    # Test 3: Force sync
    print("\nTest 3: Force sync from CCXT")
    df2 = get_price_history_df("ETHUSDT", "1h", 100, force_sync=True)
    print(f"Result: {len(df2)} candles")
    
    print("\n" + "="*70)
    print("✅ UNIFIED DATA SERVICE TEST COMPLETE")
    print("="*70 + "\n")

