"""
Train Advanced AI Model for Price Prediction
=============================================
This script trains machine learning models to predict cryptocurrency price movements.

⚠️ EDUCATIONAL DEMO - NOT FINANCIAL ADVICE ⚠️
This is a simplified ML approach for learning purposes. Real trading systems require:
- Much larger datasets (years of data)
- More sophisticated features (order book, sentiment, etc.)
- Proper validation and backtesting
- Risk management
- Regular retraining

What This Does:
1. Fetches historical OHLCV data (60-90 days)
2. Engineers features (returns, volatility, indicators)
3. Trains two models:
   - Direction Model: Predicts UP or DOWN (classification)
   - Return Model: Predicts magnitude of move (regression)
4. Saves models to disk for later use

Author: AI Trading Assistant Team
Created: 2025-11-13
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, classification_report, mean_absolute_error
import joblib
import os


def compute_simple_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute basic technical indicators for ML features
    
    Args:
        df (pd.DataFrame): OHLCV data
        
    Returns:
        pd.DataFrame: Original data with indicator columns added
        
    Indicators Explained:
        - RSI: Momentum indicator (0-100 scale)
        - MACD: Trend indicator (difference of moving averages)
        - MA_ratio: Trend strength (fast MA / slow MA)
    """
    prices = df['close']
    
    # RSI (14-period)
    # Measures momentum - how fast price is moving
    delta = prices.diff()
    gain = delta.where(delta > 0, 0).rolling(window=14).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # MACD (12,26)
    # Shows trend changes
    ema12 = prices.ewm(span=12, adjust=False).mean()
    ema26 = prices.ewm(span=26, adjust=False).mean()
    df['macd'] = ema12 - ema26
    
    # Moving Average Ratio (20 / 50)
    # > 1 = uptrend, < 1 = downtrend
    ma20 = prices.rolling(window=20).mean()
    ma50 = prices.rolling(window=50).mean()
    df['ma_ratio'] = ma20 / ma50
    
    return df


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Engineer features for machine learning model
    
    Args:
        df (pd.DataFrame): OHLCV data
        
    Returns:
        pd.DataFrame: Features for each time period
        
    Features Explained:
        1. Price Returns: How much price changed (percentage)
           - return_1h, return_3h, return_6h: Past returns
           - These capture recent momentum
        
        2. Volatility: How much price fluctuates
           - volatility_24h: Standard deviation of returns
           - High volatility = more risk, more opportunity
        
        3. Technical Indicators:
           - RSI: Overbought/oversold indicator
           - MACD: Trend strength
           - MA_ratio: Moving average relationship
        
        4. Volume:
           - volume_change: Trading activity change
           - High volume = strong conviction
    """
    # ========================================
    # 1. Price Returns (Past Performance)
    # ========================================
    # Return = (New Price - Old Price) / Old Price
    # Positive return = price went up
    # Negative return = price went down
    
    df['return_1h'] = df['close'].pct_change(1)     # 1 hour ago
    df['return_3h'] = df['close'].pct_change(3)     # 3 hours ago
    df['return_6h'] = df['close'].pct_change(6)     # 6 hours ago
    df['return_12h'] = df['close'].pct_change(12)   # 12 hours ago
    df['return_24h'] = df['close'].pct_change(24)   # 24 hours ago
    
    # ========================================
    # 2. Volatility (Price Fluctuation)
    # ========================================
    # Standard deviation of returns over last 24 periods
    # High volatility = price swings a lot (risky but profitable)
    # Low volatility = price stable (safer but less opportunity)
    
    df['volatility_24h'] = df['return_1h'].rolling(window=24).std()
    
    # ========================================
    # 3. Technical Indicators
    # ========================================
    # Add RSI, MACD, MA ratio
    df = compute_simple_indicators(df)
    
    # ========================================
    # 4. Volume Features
    # ========================================
    # Volume change = (Current Volume - Previous Volume) / Previous Volume
    # Positive = more trading activity (interest increasing)
    # Negative = less trading activity (interest decreasing)
    
    df['volume_change'] = df['volume'].pct_change(1)
    
    # ========================================
    # 5. Price Position Features
    # ========================================
    # Where is current price relative to recent high/low?
    # Close to high = strong, close to low = weak
    
    df['high_24h'] = df['high'].rolling(window=24).max()
    df['low_24h'] = df['low'].rolling(window=24).min()
    df['price_position'] = (df['close'] - df['low_24h']) / (df['high_24h'] - df['low_24h'])
    
    return df


def build_targets(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create target variables (what we want to predict)
    
    Args:
        df (pd.DataFrame): Feature data
        
    Returns:
        pd.DataFrame: Data with target columns added
        
    Targets Explained:
        1. Direction (Classification):
           - Will price go UP (1) or DOWN (0) next period?
           - Binary: just yes/no
        
        2. Return (Regression):
           - How much will price change?
           - Continuous: actual percentage (e.g., +2.3% or -1.5%)
    """
    # ========================================
    # Target 1: Direction (UP or DOWN)
    # ========================================
    # If next close > current close → UP (1)
    # If next close <= current close → DOWN (0)
    
    df['next_close'] = df['close'].shift(-1)  # Shift future price to current row
    df['direction'] = (df['next_close'] > df['close']).astype(int)
    
    # ========================================
    # Target 2: Return Magnitude
    # ========================================
    # How much did price actually change?
    # This is the percentage move we want to predict
    
    df['next_return'] = df['close'].pct_change(-1) * -1  # Future return
    
    return df


def train_models():
    """
    Main function to train ML models
    
    Steps:
        1. Fetch historical data (60-90 days)
        2. Engineer features
        3. Split train/test
        4. Train models
        5. Evaluate accuracy
        6. Save models to disk
    """
    
    print("\n" + "="*70)
    print("TRAINING ADVANCED AI PREDICTION MODELS")
    print("="*70)
    
    # ========================================
    # Step 1: Fetch Historical Data
    # ========================================
    print("\n[1/6] Fetching historical price data...")
    
    from services.advanced_data_service import AdvancedDataService
    
    data_service = AdvancedDataService()
    
    # Get 90 days of hourly BTC data (90 * 24 = 2160 data points)
    # More data = better training
    df = data_service.get_ohlcv('BTC/USDT', timeframe='1h', since_days=90)
    
    print(f"   ✅ Fetched {len(df)} candles (90 days)")
    
    if len(df) < 200:
        print("   ❌ Not enough data for training (need at least 200 candles)")
        return
    
    # ========================================
    # Step 2: Engineer Features
    # ========================================
    print("\n[2/6] Engineering features...")
    
    df = build_features(df)
    df = build_targets(df)
    
    # Remove rows with NaN values (from rolling calculations and shifts)
    df = df.dropna()
    
    print(f"   ✅ Created features, {len(df)} valid samples")
    
    # ========================================
    # Step 3: Prepare Data for Training
    # ========================================
    print("\n[3/6] Preparing training data...")
    
    # Select feature columns
    feature_columns = [
        'return_1h', 'return_3h', 'return_6h', 'return_12h', 'return_24h',
        'volatility_24h',
        'rsi', 'macd', 'ma_ratio',
        'volume_change',
        'price_position'
    ]
    
    X = df[feature_columns].values  # Features (input)
    y_direction = df['direction'].values  # Target: UP (1) or DOWN (0)
    y_return = df['next_return'].values  # Target: Return magnitude
    
    # Split into train (80%) and test (20%)
    # Train: Used to teach the model
    # Test: Used to check if model learned correctly
    X_train, X_test, y_dir_train, y_dir_test, y_ret_train, y_ret_test = train_test_split(
        X, y_direction, y_return,
        test_size=0.2,  # 20% for testing
        random_state=42  # Fixed seed for reproducibility
    )
    
    print(f"   ✅ Train samples: {len(X_train)}")
    print(f"   ✅ Test samples: {len(X_test)}")
    
    # ========================================
    # Step 4: Scale Features (Normalization)
    # ========================================
    # ML models work better when all features are on similar scale
    # StandardScaler: transforms features to have mean=0, std=1
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    print(f"   ✅ Features normalized")
    
    # ========================================
    # Step 5: Train Direction Model (Classification)
    # ========================================
    print("\n[4/6] Training direction model (UP/DOWN)...")
    
    # RandomForestClassifier: Ensemble of decision trees
    # Each tree votes, majority wins
    # Good for non-linear patterns
    
    direction_model = RandomForestClassifier(
        n_estimators=100,  # 100 trees in the forest
        max_depth=10,      # Prevent overfitting
        random_state=42,
        n_jobs=-1          # Use all CPU cores
    )
    
    direction_model.fit(X_train_scaled, y_dir_train)
    
    # Evaluate on test set
    y_dir_pred = direction_model.predict(X_test_scaled)
    direction_accuracy = accuracy_score(y_dir_test, y_dir_pred)
    
    print(f"   ✅ Direction Model Accuracy: {direction_accuracy*100:.2f}%")
    print(f"\n   Classification Report:")
    print(classification_report(y_dir_test, y_dir_pred, target_names=['DOWN', 'UP']))
    
    # ========================================
    # Step 6: Train Return Model (Regression)
    # ========================================
    print("\n[5/6] Training return magnitude model...")
    
    # RandomForestRegressor: Predicts continuous values
    # Instead of UP/DOWN, predicts actual % change
    
    return_model = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        n_jobs=-1
    )
    
    return_model.fit(X_train_scaled, y_ret_train)
    
    # Evaluate on test set
    y_ret_pred = return_model.predict(X_test_scaled)
    mae = mean_absolute_error(y_ret_test, y_ret_pred)
    
    print(f"   ✅ Return Model MAE: {mae*100:.3f}% (average error)")
    
    # ========================================
    # Step 7: Save Models to Disk
    # ========================================
    print("\n[6/6] Saving models...")
    
    # Create models directory if it doesn't exist
    models_dir = os.path.join(os.path.dirname(__file__), 'models')
    os.makedirs(models_dir, exist_ok=True)
    
    # Save models using joblib (efficient for sklearn models)
    direction_model_path = os.path.join(models_dir, 'adv_direction_model.joblib')
    return_model_path = os.path.join(models_dir, 'adv_return_model.joblib')
    scaler_path = os.path.join(models_dir, 'adv_scaler.joblib')
    
    joblib.dump(direction_model, direction_model_path)
    joblib.dump(return_model, return_model_path)
    joblib.dump(scaler, scaler_path)  # Save scaler too!
    
    # Save feature columns list (need same order when predicting)
    feature_info = {
        'feature_columns': feature_columns,
        'train_size': len(X_train),
        'test_size': len(X_test),
        'direction_accuracy': direction_accuracy,
        'return_mae': mae
    }
    
    feature_info_path = os.path.join(models_dir, 'feature_info.joblib')
    joblib.dump(feature_info, feature_info_path)
    
    print(f"   ✅ Direction model saved: {direction_model_path}")
    print(f"   ✅ Return model saved: {return_model_path}")
    print(f"   ✅ Scaler saved: {scaler_path}")
    print(f"   ✅ Feature info saved: {feature_info_path}")
    
    # ========================================
    # Summary
    # ========================================
    print("\n" + "="*70)
    print("TRAINING COMPLETE!")
    print("="*70)
    print(f"\n📊 Model Performance:")
    print(f"   • Direction Accuracy: {direction_accuracy*100:.2f}%")
    print(f"   • Return MAE: {mae*100:.3f}%")
    print(f"\n📦 Models saved to: {models_dir}")
    print(f"\n⚠️  Remember:")
    print(f"   • This is educational demo")
    print(f"   • Not financial advice")
    print(f"   • Retrain regularly with fresh data")
    print(f"   • Validate thoroughly before real use")
    print("="*70 + "\n")
    
    # ========================================
    # Feature Importance (Bonus)
    # ========================================
    print("\n📈 Top 5 Most Important Features (Direction Model):")
    feature_importance = pd.DataFrame({
        'feature': feature_columns,
        'importance': direction_model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    for i, row in feature_importance.head(5).iterrows():
        print(f"   {row['feature']:20} {row['importance']:.4f}")
    
    print("\n")


# ============================================
# MAIN EXECUTION
# ============================================

if __name__ == "__main__":
    """
    Run this script to train the models:
        python services/train_advanced_ai_model.py
    
    This will:
    1. Download 90 days of BTC/USDT data
    2. Create features from price history
    3. Train two ML models (direction + return)
    4. Save models to services/models/
    
    Run this periodically (weekly/monthly) to retrain with new data.
    """
    
    print("\n⚠️  DISCLAIMER ⚠️")
    print("This is an educational demo for learning ML in trading.")
    print("NOT financial advice. Use at your own risk.")
    print("Real trading requires much more sophisticated models.\n")
    
    input("Press Enter to start training... ")
    
    try:
        train_models()
        print("\n✅ All done! Models are ready to use.\n")
    except Exception as e:
        print(f"\n❌ Error during training: {e}")
        import traceback
        traceback.print_exc()

