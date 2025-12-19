"""
Add Price Data to SQLite Database
Inserts sample price data so AI predictions work.
"""

from models import db

print("=" * 70)
print("Adding Price Data to Database")
print("=" * 70)

# Sample price data for BTCUSDT (Bitcoin)
price_data = [
    ('BTCUSDT', '2025-11-13 09:00:00', 45000.00, 45500.00, 44800.00, 45200.00, 1250.50),
    ('BTCUSDT', '2025-11-13 10:00:00', 45200.00, 45800.00, 45100.00, 45600.00, 1380.75),
    ('BTCUSDT', '2025-11-13 11:00:00', 45600.00, 46000.00, 45400.00, 45900.00, 1520.25),
    ('BTCUSDT', '2025-11-13 12:00:00', 45900.00, 46200.00, 45700.00, 46000.00, 1620.30),
    ('BTCUSDT', '2025-11-13 13:00:00', 46000.00, 46500.00, 45800.00, 46300.00, 1750.40),
    ('BTCUSDT', '2025-11-13 14:00:00', 46300.00, 46800.00, 46100.00, 46600.00, 1850.60),
    ('BTCUSDT', '2025-11-13 15:00:00', 46600.00, 47000.00, 46400.00, 46800.00, 1920.80),
    ('BTCUSDT', '2025-11-13 16:00:00', 46800.00, 47200.00, 46500.00, 47000.00, 2010.90),
    ('BTCUSDT', '2025-11-13 17:00:00', 47000.00, 47500.00, 46900.00, 47200.00, 2150.00),
    ('BTCUSDT', '2025-11-13 18:00:00', 47200.00, 47800.00, 47000.00, 47600.00, 2280.50),
]

print(f"\n[1] Deleting old price data...")
delete_query = "DELETE FROM price_history"
db.execute_query(delete_query)
print("✅ Old data cleared")

print(f"\n[2] Inserting {len(price_data)} price records...")
query = """
    INSERT INTO price_history (symbol, timestamp, open_price, high_price, low_price, close_price, volume)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
"""

for data in price_data:
    db.execute_query(query, data)

print(f"✅ Inserted {len(price_data)} price records")

print(f"\n[3] Verifying data...")
verify_query = "SELECT COUNT(*) as count FROM price_history WHERE symbol = %s"
result = db.fetch_one(verify_query, ('BTCUSDT',))
count = result['count'] if result else 0

print(f"✅ Total BTCUSDT records in database: {count}")

print("\n" + "=" * 70)
print("✅ PRICE DATA ADDED SUCCESSFULLY!")
print("=" * 70)
print("\nYou can now:")
print("  1. Refresh the dashboard")
print("  2. Click 'Get New Prediction'")
print("  3. See AI predictions working!")
print("=" * 70)

