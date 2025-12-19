"""
Fix Price Data - Add Sufficient Historical Data for Indicators
===============================================================
Adds 300 candles of realistic price data for technical indicators (EMA 200 needs at least 200)
"""

from models import db
import random
from datetime import datetime, timedelta

print("=" * 80)
print("FIXING PRICE DATA FOR TECHNICAL INDICATORS")
print("=" * 80)

# Configuration
SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT']
NUM_CANDLES = 300  # Enough for EMA 200 (need 200 minimum)
TIMEFRAME_HOURS = 1  # 1 hour candles

# Base prices for each symbol
BASE_PRICES = {
    'BTCUSDT': 45000.00,
    'ETHUSDT': 2400.00,
    'BNBUSDT': 320.00,
    'SOLUSDT': 95.00,
    'XRPUSDT': 0.65
}

print(f"\n[1] Clearing old price data...")
db.execute_query("DELETE FROM price_history")
print("✅ Old data cleared")

print(f"\n[2] Generating {NUM_CANDLES} candles for {len(SYMBOLS)} symbols...")

total_inserted = 0

for symbol in SYMBOLS:
    print(f"\n   📊 Generating data for {symbol}...")
    
    base_price = BASE_PRICES[symbol]
    current_price = base_price
    
    # Start from 300 hours ago
    start_time = datetime.now() - timedelta(hours=NUM_CANDLES)
    
    for i in range(NUM_CANDLES):
        timestamp = start_time + timedelta(hours=i * TIMEFRAME_HOURS)
        
        # Simulate realistic price movement (random walk with mean reversion)
        # Price changes are small and centered around the base price
        volatility = random.uniform(-0.008, 0.008)  # -0.8% to +0.8% per hour
        
        # Mean reversion: if price is too far from base, pull it back slightly
        distance_from_base = (current_price - base_price) / base_price
        mean_reversion = -distance_from_base * 0.002  # Gentle pull back
        
        open_price = current_price
        close_price = current_price * (1 + volatility + mean_reversion)
        
        # Ensure price doesn't go negative or too extreme
        close_price = max(close_price, base_price * 0.7)  # Not below 70% of base
        close_price = min(close_price, base_price * 1.3)  # Not above 130% of base
        
        # High and low with realistic wicks
        high_price = max(open_price, close_price) * (1 + random.uniform(0, 0.005))
        low_price = min(open_price, close_price) * (1 - random.uniform(0, 0.005))
        
        # Volume varies
        volume = random.uniform(500, 2500)
        
        # Insert into database
        query = """
            INSERT INTO price_history 
            (symbol, timestamp, open_price, high_price, low_price, close_price, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        db.execute_query(query, (
            symbol,
            timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            round(open_price, 8),
            round(high_price, 8),
            round(low_price, 8),
            round(close_price, 8),
            round(volume, 2)
        ))
        
        current_price = close_price
        total_inserted += 1
    
    print(f"      ✅ {symbol}: {NUM_CANDLES} candles inserted")
    print(f"         Starting price: ${base_price:.2f}")
    print(f"         Ending price:   ${current_price:.2f}")
    print(f"         Change: {((current_price - base_price) / base_price * 100):+.2f}%")

print(f"\n[3] Verifying data...")
for symbol in SYMBOLS:
    verify = db.fetch_one(
        "SELECT COUNT(*) as count FROM price_history WHERE symbol = ?", 
        (symbol,)
    )
    count = verify['count'] if verify else 0
    print(f"   ✅ {symbol}: {count} candles")

print(f"\n✅ Total records inserted: {total_inserted}")

print("\n" + "=" * 80)
print("✅ PRICE DATA FIXED!")
print("=" * 80)
print(f"\nYou now have {NUM_CANDLES} candles for each symbol, which is enough for:")
print("  ✅ EMA 200 (needs 200 minimum)")
print("  ✅ All technical indicators")
print("  ✅ MA Trading Signals")
print("  ✅ AI Predictions")
print("  ✅ Chart visualizations")
print("\nRefresh your browser to see Technical Indicators and MA Trading Signals!")
print("=" * 80)

