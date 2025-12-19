"""
Advanced AI Predictor
=====================
Uses trained ML models to predict cryptocurrency price movements.

⚠️ EDUCATIONAL DEMO - NOT FINANCIAL ADVICE ⚠️

This module loads pre-trained scikit-learn models and makes predictions on new data.
The models were trained on historical OHLCV data and predict:
1. Direction: Will price go UP or DOWN?
2. Magnitude: How much will price change (percentage)?

Author: AI Trading Assistant Team
Created: 2025-11-13
"""

import pandas as pd
import numpy as np
import joblib
import os
from datetime import timedelta


# ============================================
# MODEL LOADING
# ============================================

# Global variables to hold loaded models
# These are loaded once when module is imported
DIRECTION_MODEL = None
RETURN_MODEL = None
SCALER = None
FEATURE_INFO = None

def load_models():
    """
    Load trained models from disk
    
    This function is called automatically when the module is imported.
    Models are loaded into global variables for reuse.
    
    Models Loaded:
        - Direction Model: Predicts UP (1) or DOWN (0)
        - Return Model: Predicts magnitude of price change (%)
        - Scaler: Normalizes features to match training scale
        - Feature Info: Column names and order
    """
    global DIRECTION_MODEL, RETURN_MODEL, SCALER, FEATURE_INFO
    
    # Path to models directory
    models_dir = os.path.join(os.path.dirname(__file__), 'models')
    
    direction_path = os.path.join(models_dir, 'adv_direction_model.joblib')
    return_path = os.path.join(models_dir, 'adv_return_model.joblib')
    scaler_path = os.path.join(models_dir, 'adv_scaler.joblib')
    feature_info_path = os.path.join(models_dir, 'feature_info.joblib')
    
    # Check if models exist
    if not os.path.exists(direction_path):
        print(f"⚠️  Models not found in {models_dir}")
        print(f"   Please run: python services/train_advanced_ai_model.py")
        return False
    
    # Load models
    try:
        DIRECTION_MODEL = joblib.load(direction_path)
        RETURN_MODEL = joblib.load(return_path)
        SCALER = joblib.load(scaler_path)
        FEATURE_INFO = joblib.load(feature_info_path)
        
        print(f"✅ AI models loaded successfully")
        print(f"   Direction accuracy: {FEATURE_INFO['direction_accuracy']*100:.1f}%")
        print(f"   Return MAE: {FEATURE_INFO['return_mae']*100:.2f}%")
        
        return True
    except Exception as e:
        print(f"❌ Error loading models: {e}")
        return False


# Try to load models on import
# If models don't exist, user needs to train them first
load_models()


# ============================================
# FEATURE ENGINEERING (Match Training)
# ============================================

def compute_simple_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute technical indicators (same as training)
    
    IMPORTANT: Must match exactly what was used in training!
    """
    prices = df['close']
    
    # RSI (14-period)
    delta = prices.diff()
    gain = delta.where(delta > 0, 0).rolling(window=14).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # MACD (12,26)
    ema12 = prices.ewm(span=12, adjust=False).mean()
    ema26 = prices.ewm(span=26, adjust=False).mean()
    df['macd'] = ema12 - ema26
    
    # Moving Average Ratio (20 / 50)
    ma20 = prices.rolling(window=20).mean()
    ma50 = prices.rolling(window=50).mean()
    df['ma_ratio'] = ma20 / ma50
    
    return df


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Engineer features (same as training)
    
    IMPORTANT: Must match exactly what was used in training!
    """
    # Price Returns
    df['return_1h'] = df['close'].pct_change(1)
    df['return_3h'] = df['close'].pct_change(3)
    df['return_6h'] = df['close'].pct_change(6)
    df['return_12h'] = df['close'].pct_change(12)
    df['return_24h'] = df['close'].pct_change(24)
    
    # Volatility
    df['volatility_24h'] = df['return_1h'].rolling(window=24).std()
    
    # Technical Indicators
    df = compute_simple_indicators(df)
    
    # Volume Features
    df['volume_change'] = df['volume'].pct_change(1)
    
    # Price Position
    df['high_24h'] = df['high'].rolling(window=24).max()
    df['low_24h'] = df['low'].rolling(window=24).min()
    df['price_position'] = (df['close'] - df['low_24h']) / (df['high_24h'] - df['low_24h'])
    
    return df


# ============================================
# PREDICTION FUNCTION
# ============================================

def advanced_ai_predict(symbol: str, timeframe: str = "1h") -> dict:
    """
    Make AI-based prediction for a cryptocurrency
    
    Args:
        symbol (str): Trading pair (e.g., 'BTC/USDT')
        timeframe (str): Candle interval ('1h', '4h', '1d')
        
    Returns:
        dict: Prediction result with signal, target, confidence, and chart
        
    How It Works:
        1. Fetches recent price history
        2. Computes same features as training
        3. Normalizes features using saved scaler
        4. Runs through ML models:
           - Direction model → Probability of UP
           - Return model → Expected % change
        5. Generates trading signal based on probabilities
        6. Creates natural language summary
        
    Signal Logic:
        - prob_up > 0.55 → BUY (model is confident price goes up)
        - prob_up < 0.45 → SELL (model is confident price goes down)
        - 0.45 ≤ prob_up ≤ 0.55 → HOLD (model is uncertain)
        
    Example:
        >>> result = advanced_ai_predict('BTC/USDT', '1h')
        >>> print(f"{result['signal']}: {result['summary']}")
    """
    
    # Check if models are loaded
    if DIRECTION_MODEL is None or RETURN_MODEL is None:
        return {
            'mode': 'ai',
            'symbol': symbol,
            'timeframe': timeframe,
            'signal': 'HOLD',
            'error': 'Models not loaded. Please train models first.',
            'summary': 'AI models not available. Run train_advanced_ai_model.py to train them.'
        }
    
    print(f"\n{'='*70}")
    print(f"ADVANCED AI PREDICTION")
    print(f"{'='*70}")
    print(f"Symbol: {symbol}")
    print(f"Timeframe: {timeframe}")
    print(f"{'='*70}\n")
    
    # ========================================
    # Step 1: Fetch Price Data
    # ========================================
    print(f"[1/6] Fetching price data...")
    
    from services.advanced_data_service import AdvancedDataService
    
    data_service = AdvancedDataService()
    df = data_service.get_ohlcv(symbol, timeframe, since_days=30)
    
    if len(df) < 50:
        return {
            'mode': 'ai',
            'symbol': symbol,
            'timeframe': timeframe,
            'signal': 'HOLD',
            'error': 'Insufficient data',
            'summary': f'Only {len(df)} candles available. Need at least 50.'
        }
    
    print(f"   ✅ Fetched {len(df)} candles")
    
    # ========================================
    # Step 2: Engineer Features
    # ========================================
    print(f"[2/6] Engineering features...")
    
    df = build_features(df)
    df = df.dropna()  # Remove rows with NaN
    
    if len(df) == 0:
        return {
            'mode': 'ai',
            'symbol': symbol,
            'signal': 'HOLD',
            'error': 'No valid data after feature engineering',
            'summary': 'Unable to compute features from data.'
        }
    
    print(f"   ✅ Features computed")
    
    # ========================================
    # Step 3: Extract Latest Features
    # ========================================
    print(f"[3/6] Preparing features for prediction...")
    
    # Get feature columns from training
    feature_columns = FEATURE_INFO['feature_columns']
    
    # Extract latest row features
    latest_features = df[feature_columns].iloc[-1].values.reshape(1, -1)
    
    # Normalize using saved scaler
    # IMPORTANT: Must use same scaler as training!
    latest_features_scaled = SCALER.transform(latest_features)
    
    # Get current price
    current_price = float(df['close'].iloc[-1])
    
    print(f"   ✅ Current price: ${current_price:.2f}")
    
    # ========================================
    # Step 4: Make Predictions
    # ========================================
    print(f"[4/6] Running AI models...")
    
    # Direction prediction (probability of UP)
    # Returns array like [[prob_down, prob_up]]
    prob_direction = DIRECTION_MODEL.predict_proba(latest_features_scaled)[0]
    prob_down = prob_direction[0]
    prob_up = prob_direction[1]
    
    # Return magnitude prediction (expected % change)
    predicted_return = RETURN_MODEL.predict(latest_features_scaled)[0]
    
    print(f"   ✅ Probability UP: {prob_up*100:.1f}%")
    print(f"   ✅ Probability DOWN: {prob_down*100:.1f}%")
    print(f"   ✅ Expected return: {predicted_return*100:+.2f}%")
    
    # ========================================
    # Step 5: Generate Signal
    # ========================================
    print(f"[5/6] Generating trading signal...")
    
    # Determine signal based on probability
    # High confidence = probability far from 50%
    if prob_up > 0.55:
        signal = "BUY"
        # Use predicted return, but clip to reasonable range
        expected_change_pct = max(min(abs(predicted_return) * 100, 10), 1)
    elif prob_up < 0.45:
        signal = "SELL"
        expected_change_pct = -max(min(abs(predicted_return) * 100, 10), 1)
    else:
        signal = "HOLD"
        expected_change_pct = 0
    
    # Calculate target price
    target_price = current_price * (1 + expected_change_pct / 100)
    
    # Confidence = how far probability is from 50% (uncertain)
    # If prob = 0.8 → confidence = 80%
    # If prob = 0.5 → confidence = 50% (very uncertain)
    confidence = max(prob_up, prob_down) * 100
    
    # Time horizon based on timeframe
    if timeframe == '1h':
        horizon = "next 1-4 hours"
    elif timeframe == '4h':
        horizon = "next 4-12 hours"
    else:
        horizon = "next 1-2 days"
    
    print(f"   ✅ Signal: {signal}")
    print(f"   ✅ Target: ${target_price:.2f} ({expected_change_pct:+.1f}%)")
    print(f"   ✅ Confidence: {confidence:.1f}%")
    
    # ========================================
    # Step 6: Build Summary
    # ========================================
    
    # Create natural language explanation
    if signal == "BUY":
        summary = (
            f"AI model predicts ~{expected_change_pct:+.1f}% move up in {horizon} "
            f"(probability {prob_up*100:.0f}%). "
            f"Suggestion: BUY near current levels (${current_price:.2f}) "
            f"and target ${target_price:.2f}. "
            f"Confidence: {confidence:.0f}%."
        )
    elif signal == "SELL":
        summary = (
            f"AI model predicts ~{expected_change_pct:.1f}% move down in {horizon} "
            f"(probability {prob_down*100:.0f}%). "
            f"Suggestion: SELL near current levels (${current_price:.2f}) "
            f"and target ${target_price:.2f}. "
            f"Confidence: {confidence:.0f}%."
        )
    else:
        summary = (
            f"AI model is uncertain (probability split {prob_up*100:.0f}%/{prob_down*100:.0f}%). "
            f"Suggestion: HOLD and wait for clearer signals. "
            f"Current price: ${current_price:.2f}."
        )
    
    # ========================================
    # Step 7: Prepare Chart Data
    # ========================================
    
    # Get last 50 candles for chart
    chart_df = df.tail(50)
    
    timestamps = [ts.isoformat() for ts in chart_df.index]
    prices = [float(p) for p in chart_df['close'].values]
    
    # Add future prediction point
    future_timestamp = chart_df.index[-1] + timedelta(hours=24)
    timestamps.append(future_timestamp.isoformat())
    
    # Prediction line (None for historical, target for future)
    prediction_line = [None] * len(prices)
    prediction_line.append(target_price)
    
    # ========================================
    # Step 8: Build Result Dictionary
    # ========================================
    
    result = {
        'mode': 'ai',
        'symbol': symbol,
        'timeframe': timeframe,
        'signal': signal,
        'target_price': round(target_price, 2),
        'expected_change_pct': round(expected_change_pct, 2),
        'confidence': round(confidence, 1),
        'horizon': horizon,
        'current_price': round(current_price, 2),
        'probabilities': {
            'up': round(prob_up * 100, 1),
            'down': round(prob_down * 100, 1)
        },
        'predicted_return': round(predicted_return * 100, 2),
        'summary': summary,
        'chart': {
            'timestamps': timestamps,
            'prices': prices,
            'prediction': prediction_line
        },
        'model_info': {
            'direction_accuracy': round(FEATURE_INFO['direction_accuracy'] * 100, 1),
            'return_mae': round(FEATURE_INFO['return_mae'] * 100, 2)
        }
    }
    
    print(f"\n{'='*70}")
    print(f"✅ AI PREDICTION COMPLETE")
    print(f"{'='*70}")
    print(f"Signal: {result['signal']}")
    print(f"Current: ${result['current_price']:.2f}")
    print(f"Target: ${result['target_price']:.2f} ({result['expected_change_pct']:+.1f}%)")
    print(f"Confidence: {result['confidence']:.1f}%")
    print(f"Horizon: {result['horizon']}")
    print(f"\nSummary:")
    print(f"{result['summary']}")
    print(f"{'='*70}\n")
    
    return result


# ============================================
# HELPER FUNCTIONS
# ============================================

def print_prediction_summary(result: dict):
    """
    Pretty-print prediction result
    
    Args:
        result (dict): Result from advanced_ai_predict()
    """
    print(f"\n{'='*70}")
    print(f"AI PREDICTION SUMMARY")
    print(f"{'='*70}")
    print(f"Symbol: {result['symbol']}")
    print(f"Timeframe: {result['timeframe']}")
    print(f"")
    print(f"🤖 SIGNAL: {result['signal']}")
    print(f"💰 Current Price: ${result['current_price']:.2f}")
    print(f"🎯 Target Price: ${result['target_price']:.2f}")
    print(f"📈 Expected Change: {result['expected_change_pct']:+.1f}%")
    print(f"✅ Confidence: {result['confidence']:.1f}%")
    print(f"⏰ Time Horizon: {result['horizon']}")
    print(f"")
    print(f"📊 Probabilities:")
    print(f"   UP: {result['probabilities']['up']:.1f}%")
    print(f"   DOWN: {result['probabilities']['down']:.1f}%")
    print(f"")
    print(f"📝 SUMMARY:")
    print(f"{result['summary']}")
    print(f"{'='*70}\n")


# ============================================
# EXAMPLE USAGE
# ============================================

if __name__ == "__main__":
    """
    Test the AI predictor
    
    Run this file directly to test:
        python services/advanced_ai_predictor.py
    """
    
    print("\n⚠️  Make sure you've trained the models first!")
    print("   Run: python services/train_advanced_ai_model.py\n")
    
    # Example 1: Bitcoin 1-hour
    print("\n🤖 Testing Bitcoin (BTC/USDT) - 1 hour timeframe\n")
    btc_result = advanced_ai_predict('BTC/USDT', '1h')
    
    if 'error' not in btc_result:
        print_prediction_summary(btc_result)
    else:
        print(f"❌ Error: {btc_result['error']}")
    
    print("\n✅ Test complete!")

