"""
Add Historical Price Data
Generates 60 days of realistic price data for technical indicator calculations.
"""

from models import db
import random
from datetime import datetime, timedelta

print("=" * 70)
print("Adding Historical Price Data for Indicators")
print("=" * 70)

# Clear old data
print("\n[1] Clearing old price data...")
db.execute_query("DELETE FROM price_history")
print("✅ Old data cleared")

# Generate 60 days of hourly data
print("\n[2] Generating 60 records of price data...")

base_price = 45000.00
current_price = base_price
start_date = datetime.now() - timedelta(days=3)

prices = []

for i in range(60):
    timestamp = start_date + timedelta(hours=i)
    
    # Random price movement
    change_pct = random.uniform(-0.02, 0.02)  # -2% to +2%
    open_price = current_price
    close_price = current_price * (1 + change_pct)
    
    high_price = max(open_price, close_price) * (1 + random.uniform(0, 0.01))
    low_price = min(open_price, close_price) * (1 - random.uniform(0, 0.01))
    
    volume = random.uniform(1000, 2000)
    
    prices.append({
        'symbol': 'BTCUSDT',
        'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'open_price': round(open_price, 2),
        'high_price': round(high_price, 2),
        'low_price': round(low_price, 2),
        'close_price': round(close_price, 2),
        'volume': round(volume, 2)
    })
    
    current_price = close_price

# Insert into database
print(f"[3] Inserting {len(prices)} records into database...")

query = """
    INSERT INTO price_history (symbol, timestamp, open_price, high_price, low_price, close_price, volume)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
"""

for price in prices:
    db.execute_query(query, (
        price['symbol'],
        price['timestamp'],
        price['open_price'],
        price['high_price'],
        price['low_price'],
        price['close_price'],
        price['volume']
    ))

print(f"✅ Inserted {len(prices)} price records")

# Verify
print("\n[4] Verifying data...")
verify = db.fetch_one("SELECT COUNT(*) as count FROM price_history WHERE symbol = %s", ('BTCUSDT',))
count = verify['count'] if verify else 0

print(f"✅ Total BTCUSDT records: {count}")
print(f"   Price range: ${prices[0]['close_price']:.2f} to ${prices[-1]['close_price']:.2f}")

print("\n" + "=" * 70)
print("✅ HISTORICAL PRICE DATA ADDED!")
print("=" * 70)
print("\nYou now have enough data for:")
print("  - Technical indicators (SMA, RSI)")
print("  - AI predictions")
print("  - Chart visualization")
print("\nRefresh your dashboard to see indicators!")
print("=" * 70)

