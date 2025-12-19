"""
Prediction Service
Uses the trained AI model to make price predictions.
"""

import numpy as np
import pandas as pd
from services.train_model import load_model
from models import db


def predict_price_movement(symbol='BTCUSDT', model_path='services/model.joblib'):
    """
    Predict if the price will go UP or DOWN for a given symbol.
    
    Args:
        symbol (str): Cryptocurrency symbol (e.g., 'BTCUSDT')
        model_path (str): Path to the trained model
    
    Returns:
        dict: Prediction result with keys:
            - prediction: 1 (UP) or 0 (DOWN)
            - confidence: Confidence score (0.0 to 1.0)
            - direction: 'UP' or 'DOWN'
            - confidence_pct: Confidence as percentage
    """
    # Load the trained model
    model_data = load_model(model_path)
    
    if model_data is None:
        return None
    
    model = model_data['model']
    scaler = model_data['scaler']
    feature_columns = model_data['features']
    
    # ========================================
    # Get Recent Price Data
    # ========================================
    
    # Query last 10 price records for this symbol
    query = """
        SELECT * FROM price_history
        WHERE symbol = ?
        ORDER BY timestamp DESC
        LIMIT 10
    """
    prices = db.fetch_all(query, (symbol,))
    
    if not prices or len(prices) < 7:
        print(f"❌ Not enough price data for {symbol} (need at least 7 records)")
        return None
    
    # Convert to DataFrame and sort by timestamp (oldest first)
    df = pd.DataFrame(prices)
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    # ========================================
    # Calculate Features (same as training)
    # ========================================
    
    # Feature 1: Previous close
    df['prev_close'] = df['close_price'].shift(1)
    
    # Feature 2: Return
    df['return'] = (df['close_price'] - df['prev_close']) / df['prev_close']
    
    # Feature 3: SMA 5
    df['sma_5'] = df['close_price'].rolling(window=5).mean()
    
    # Feature 4: Distance from SMA
    df['distance_from_sma'] = (df['close_price'] - df['sma_5']) / df['sma_5']
    
    # Feature 5: Volatility
    df['volatility'] = df['return'].rolling(window=5).std()
    
    # Feature 6: High-low range
    df['high_low_range'] = (df['high_price'] - df['low_price']) / df['close_price']
    
    # Feature 7: Volume
    df['volume_normalized'] = df['volume']
    
    # Get the most recent row (after calculating all features)
    df_clean = df.dropna()
    
    if len(df_clean) == 0:
        print(f"❌ Not enough data to calculate features for {symbol}")
        return None
    
    # Get the latest row
    latest = df_clean.iloc[-1]
    
    # Prepare features for prediction
    features = [
        latest['prev_close'],
        latest['return'],
        latest['sma_5'],
        latest['distance_from_sma'],
        latest['volatility'],
        latest['high_low_range'],
        latest['volume_normalized']
    ]
    
    # Convert to numpy array and reshape
    X = np.array(features).reshape(1, -1)
    
    # Scale features
    X_scaled = scaler.transform(X)
    
    # ========================================
    # Make Prediction
    # ========================================
    
    # Predict class (0 or 1)
    prediction = model.predict(X_scaled)[0]
    
    # Get probability scores
    probabilities = model.predict_proba(X_scaled)[0]
    
    # Confidence is the probability of the predicted class
    confidence = probabilities[prediction]
    
    # Create result
    result = {
        'prediction': int(prediction),
        'confidence': float(confidence),
        'direction': 'UP' if prediction == 1 else 'DOWN',
        'confidence_pct': round(confidence * 100, 1),
        'symbol': symbol,
        'current_price': float(latest['close_price']),
        'probabilities': {
            'down': float(probabilities[0]),
            'up': float(probabilities[1])
        }
    }
    
    return result


def save_prediction_to_db(symbol, prediction_class, confidence):
    """
    Save a prediction to the database.
    
    Args:
        symbol (str): Cryptocurrency symbol
        prediction_class (int): 1 for UP, 0 for DOWN
        confidence (float): Confidence score (0.0 to 1.0)
    
    Returns:
        int: Prediction ID if successful, None otherwise
    """
    query = """
        INSERT INTO predictions (symbol, prediction_class, confidence)
        VALUES (?, ?, ?)
    """
    prediction_id = db.execute_query(query, (symbol, prediction_class, confidence))
    return prediction_id


def get_latest_prediction(symbol):
    """
    Get the latest prediction for a symbol from the database.
    
    Args:
        symbol (str): Cryptocurrency symbol
    
    Returns:
        dict: Prediction data or None
    """
    query = """
        SELECT * FROM predictions
        WHERE symbol = ?
        ORDER BY timestamp DESC
        LIMIT 1
    """
    prediction = db.fetch_one(query, (symbol,))
    
    if prediction:
        # Add human-readable direction
        prediction['direction'] = 'UP' if prediction['prediction_class'] == 1 else 'DOWN'
        prediction['confidence_pct'] = round(prediction['confidence'] * 100, 1)
    
    return prediction


def generate_and_save_prediction(symbol='BTCUSDT'):
    """
    Generate a prediction and save it to the database.
    
    Args:
        symbol (str): Cryptocurrency symbol
    
    Returns:
        dict: Prediction result or None
    """
    # Generate prediction
    result = predict_price_movement(symbol)
    
    if result:
        # Save to database
        prediction_id = save_prediction_to_db(
            symbol=symbol,
            prediction_class=result['prediction'],
            confidence=result['confidence']
        )
        
        if prediction_id:
            result['prediction_id'] = prediction_id
            print(f"✅ Prediction saved to database (ID: {prediction_id})")
        
        return result
    
    return None


# ========================================
# Testing Function
# ========================================

if __name__ == "__main__":
    print("=" * 70)
    print("AI PREDICTION SERVICE - TEST")
    print("=" * 70)
    
    # Test prediction
    print("\n[1] Making prediction for BTCUSDT...")
    result = predict_price_movement('BTCUSDT')
    
    if result:
        print(f"\n✅ Prediction Result:")
        print(f"   Symbol: {result['symbol']}")
        print(f"   Current Price: ${result['current_price']:,.2f}")
        print(f"   Prediction: {result['direction']}")
        print(f"   Confidence: {result['confidence_pct']}%")
        print(f"\n   Probabilities:")
        print(f"   - DOWN: {result['probabilities']['down']*100:.1f}%")
        print(f"   - UP: {result['probabilities']['up']*100:.1f}%")
        
        # Save to database
        print(f"\n[2] Saving prediction to database...")
        prediction_id = save_prediction_to_db(
            result['symbol'],
            result['prediction'],
            result['confidence']
        )
        
        if prediction_id:
            print(f"✅ Prediction saved with ID: {prediction_id}")
    else:
        print("❌ Prediction failed")
        print("   Make sure:")
        print("   - Model is trained (run: python services/train_model.py)")
        print("   - Price data exists in database")
    
    print("\n" + "=" * 70)

