"""
Create Sample Price Data
Generates realistic cryptocurrency price data for training the AI model.

This creates synthetic price data that mimics real crypto price movements.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os


def create_sample_data(num_records=500, output_path='data/sample_prices.csv'):
    """
    Create sample cryptocurrency price data.
    
    Args:
        num_records (int): Number of price records to generate
        output_path (str): Path to save the CSV file
    
    Returns:
        pd.DataFrame: The generated price data
    """
    print("=" * 70)
    print("CREATING SAMPLE PRICE DATA")
    print("=" * 70)
    
    print(f"\n[1] Generating {num_records} price records...")
    
    # Set random seed for reproducibility
    np.random.seed(42)
    
    # Starting parameters
    start_price = 45000.0  # Starting Bitcoin price
    start_date = datetime(2025, 1, 1, 0, 0, 0)
    
    # Lists to store data
    timestamps = []
    opens = []
    highs = []
    lows = []
    closes = []
    volumes = []
    
    current_price = start_price
    
    for i in range(num_records):
        # Generate timestamp (hourly data)
        timestamp = start_date + timedelta(hours=i)
        timestamps.append(timestamp.strftime('%Y-%m-%d %H:%M:%S'))
        
        # Generate open price (close to previous close)
        open_price = current_price * (1 + np.random.normal(0, 0.002))
        
        # Generate price movement for this period
        # Use random walk with slight upward bias
        price_change_pct = np.random.normal(0.001, 0.01)  # Mean 0.1% up, std 1%
        close_price = open_price * (1 + price_change_pct)
        
        # Generate high and low
        # High is above both open and close
        high_price = max(open_price, close_price) * (1 + abs(np.random.normal(0, 0.005)))
        # Low is below both open and close
        low_price = min(open_price, close_price) * (1 - abs(np.random.normal(0, 0.005)))
        
        # Generate volume (random but somewhat correlated with price movement)
        base_volume = 1000
        volume = base_volume * (1 + abs(price_change_pct) * 10 + np.random.normal(0, 0.5))
        volume = max(100, volume)  # Minimum volume
        
        # Add to lists
        opens.append(round(open_price, 2))
        highs.append(round(high_price, 2))
        lows.append(round(low_price, 2))
        closes.append(round(close_price, 2))
        volumes.append(round(volume, 2))
        
        # Update current price for next iteration
        current_price = close_price
    
    print(f"✅ Generated price data:")
    print(f"   - Start price: ${opens[0]:,.2f}")
    print(f"   - End price: ${closes[-1]:,.2f}")
    print(f"   - Change: {((closes[-1] - opens[0]) / opens[0] * 100):+.2f}%")
    print(f"   - Highest: ${max(highs):,.2f}")
    print(f"   - Lowest: ${min(lows):,.2f}")
    
    # ========================================
    # Create DataFrame
    # ========================================
    print(f"\n[2] Creating DataFrame...")
    
    df = pd.DataFrame({
        'timestamp': timestamps,
        'open': opens,
        'high': highs,
        'low': lows,
        'close': closes,
        'volume': volumes
    })
    
    print(f"✅ DataFrame created with {len(df)} rows")
    print(f"\nFirst few rows:")
    print(df.head())
    
    # ========================================
    # Save to CSV
    # ========================================
    print(f"\n[3] Saving to CSV...")
    
    # Create data directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    
    print(f"✅ Data saved to: {output_path}")
    
    # ========================================
    # Statistics
    # ========================================
    print(f"\n[4] Data Statistics:")
    print(f"   - Number of records: {len(df)}")
    print(f"   - Date range: {df['timestamp'].iloc[0]} to {df['timestamp'].iloc[-1]}")
    print(f"   - Average close: ${df['close'].mean():,.2f}")
    print(f"   - Std deviation: ${df['close'].std():,.2f}")
    print(f"   - Average volume: {df['volume'].mean():,.2f}")
    
    # Calculate UP vs DOWN movements
    df['next_close'] = df['close'].shift(-1)
    df['direction'] = (df['next_close'] > df['close']).astype(int)
    up_count = df['direction'].sum()
    down_count = len(df) - up_count - 1  # -1 for last row
    
    print(f"\n[5] Price Movements:")
    print(f"   - UP movements: {up_count} ({up_count/(up_count+down_count)*100:.1f}%)")
    print(f"   - DOWN movements: {down_count} ({down_count/(up_count+down_count)*100:.1f}%)")
    
    print("\n" + "=" * 70)
    print("✅ SAMPLE DATA CREATED SUCCESSFULLY!")
    print("=" * 70)
    print(f"\nYou can now train the model:")
    print(f"  python services/train_model.py")
    print("=" * 70)
    
    return df


if __name__ == "__main__":
    # Create sample data when script is executed directly
    create_sample_data(num_records=500)

