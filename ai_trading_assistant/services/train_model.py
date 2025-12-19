"""
AI Model Training Script
Trains a simple machine learning model to predict if cryptocurrency price will go UP or DOWN.

The model uses basic technical indicators to make predictions:
- Previous close price
- Price returns
- Moving averages
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib
import os


def train_model(data_path='data/sample_prices.csv', model_path='services/model.joblib'):
    """
    Train a machine learning model to predict price movements.
    
    Args:
        data_path (str): Path to CSV file with price data
        model_path (str): Path to save the trained model
    
    Returns:
        tuple: (model, scaler, accuracy) - The trained model, scaler, and accuracy score
    """
    print("=" * 70)
    print("AI TRADING MODEL TRAINING")
    print("=" * 70)
    
    # ========================================
    # STEP 1: Load Data
    # ========================================
    print("\n[Step 1] Loading price data...")
    
    if not os.path.exists(data_path):
        print(f"❌ Error: Data file not found at {data_path}")
        print(f"   Please create sample data first.")
        return None, None, None
    
    # Read CSV file into pandas DataFrame
    df = pd.read_csv(data_path)
    print(f"✅ Loaded {len(df)} price records")
    print(f"   Columns: {list(df.columns)}")
    
    # ========================================
    # STEP 2: Feature Engineering
    # ========================================
    print("\n[Step 2] Creating features...")
    
    # Sort by timestamp to ensure correct order
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    # Feature 1: Previous close price
    # This helps the model understand the current price level
    df['prev_close'] = df['close'].shift(1)
    
    # Feature 2: Price return (percentage change)
    # This shows how much the price moved
    df['return'] = (df['close'] - df['prev_close']) / df['prev_close']
    
    # Feature 3: Simple Moving Average (SMA) over last 5 periods
    # This smooths out price fluctuations
    df['sma_5'] = df['close'].rolling(window=5).mean()
    
    # Feature 4: Distance from moving average
    # Shows if price is above or below the trend
    df['distance_from_sma'] = (df['close'] - df['sma_5']) / df['sma_5']
    
    # Feature 5: Volatility (standard deviation of last 5 returns)
    # Higher volatility = more risk
    df['volatility'] = df['return'].rolling(window=5).std()
    
    # Feature 6: High-Low range (normalized by close)
    # Shows price movement within the period
    df['high_low_range'] = (df['high'] - df['low']) / df['close']
    
    # Feature 7: Volume (can indicate strength of movement)
    df['volume_normalized'] = df['volume']
    
    print(f"✅ Created 7 features:")
    print(f"   - prev_close: Previous closing price")
    print(f"   - return: Price return (percentage change)")
    print(f"   - sma_5: 5-period simple moving average")
    print(f"   - distance_from_sma: Distance from SMA")
    print(f"   - volatility: 5-period return volatility")
    print(f"   - high_low_range: High-low range normalized")
    print(f"   - volume_normalized: Trading volume")
    
    # ========================================
    # STEP 3: Create Target Label
    # ========================================
    print("\n[Step 3] Creating target labels...")
    
    # Target: 1 if next close > current close (UP), 0 otherwise (DOWN)
    df['next_close'] = df['close'].shift(-1)
    df['target'] = (df['next_close'] > df['close']).astype(int)
    
    # Count UP vs DOWN movements
    up_count = df['target'].sum()
    down_count = len(df) - up_count
    print(f"✅ Target labels created:")
    print(f"   - UP (1): {up_count} cases ({up_count/len(df)*100:.1f}%)")
    print(f"   - DOWN (0): {down_count} cases ({down_count/len(df)*100:.1f}%)")
    
    # ========================================
    # STEP 4: Clean Data
    # ========================================
    print("\n[Step 4] Cleaning data...")
    
    # Remove rows with NaN values (from shifting and rolling operations)
    df_clean = df.dropna()
    print(f"✅ Removed {len(df) - len(df_clean)} rows with missing values")
    print(f"   Final dataset: {len(df_clean)} rows")
    
    if len(df_clean) < 50:
        print("❌ Error: Not enough data to train model (need at least 50 rows)")
        return None, None, None
    
    # ========================================
    # STEP 5: Prepare Features and Target
    # ========================================
    print("\n[Step 5] Preparing features and target...")
    
    # Select feature columns
    feature_columns = [
        'prev_close',
        'return',
        'sma_5',
        'distance_from_sma',
        'volatility',
        'high_low_range',
        'volume_normalized'
    ]
    
    X = df_clean[feature_columns].values
    y = df_clean['target'].values
    
    print(f"✅ Feature matrix shape: {X.shape}")
    print(f"   Target vector shape: {y.shape}")
    
    # ========================================
    # STEP 6: Split Data into Train and Test
    # ========================================
    print("\n[Step 6] Splitting data into train and test sets...")
    
    # Split: 80% training, 20% testing
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"✅ Data split:")
    print(f"   - Training set: {len(X_train)} samples")
    print(f"   - Test set: {len(X_test)} samples")
    
    # ========================================
    # STEP 7: Scale Features
    # ========================================
    print("\n[Step 7] Scaling features...")
    
    # StandardScaler normalizes features to have mean=0 and std=1
    # This helps the model learn better
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    print(f"✅ Features scaled using StandardScaler")
    
    # ========================================
    # STEP 8: Train Model
    # ========================================
    print("\n[Step 8] Training Random Forest model...")
    
    # Random Forest is a good choice for classification
    # It combines multiple decision trees for better accuracy
    model = RandomForestClassifier(
        n_estimators=100,      # Number of trees
        max_depth=10,          # Maximum depth of each tree
        random_state=42,       # For reproducibility
        n_jobs=-1              # Use all CPU cores
    )
    
    # Train the model
    model.fit(X_train_scaled, y_train)
    
    print(f"✅ Model trained with {model.n_estimators} trees")
    
    # ========================================
    # STEP 9: Evaluate Model
    # ========================================
    print("\n[Step 9] Evaluating model performance...")
    
    # Make predictions on training set
    y_train_pred = model.predict(X_train_scaled)
    train_accuracy = accuracy_score(y_train, y_train_pred)
    
    # Make predictions on test set
    y_test_pred = model.predict(X_test_scaled)
    test_accuracy = accuracy_score(y_test, y_test_pred)
    
    print(f"✅ Model Performance:")
    print(f"   - Training Accuracy: {train_accuracy*100:.2f}%")
    print(f"   - Test Accuracy: {test_accuracy*100:.2f}%")
    
    # Show detailed classification report
    print(f"\n📊 Detailed Classification Report (Test Set):")
    print(classification_report(y_test, y_test_pred, 
                                target_names=['DOWN (0)', 'UP (1)'],
                                digits=3))
    
    # Show confusion matrix
    cm = confusion_matrix(y_test, y_test_pred)
    print(f"📊 Confusion Matrix:")
    print(f"                  Predicted")
    print(f"                DOWN    UP")
    print(f"   Actual DOWN   {cm[0][0]:4d}  {cm[0][1]:4d}")
    print(f"          UP     {cm[1][0]:4d}  {cm[1][1]:4d}")
    
    # Feature importance
    print(f"\n📊 Feature Importance:")
    feature_importance = pd.DataFrame({
        'feature': feature_columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    for idx, row in feature_importance.iterrows():
        print(f"   {row['feature']:20s}: {row['importance']:.4f}")
    
    # ========================================
    # STEP 10: Save Model
    # ========================================
    print(f"\n[Step 10] Saving model...")
    
    # Create services directory if it doesn't exist
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    
    # Save both model and scaler together
    model_data = {
        'model': model,
        'scaler': scaler,
        'features': feature_columns,
        'accuracy': test_accuracy
    }
    
    joblib.dump(model_data, model_path)
    print(f"✅ Model saved to: {model_path}")
    
    # ========================================
    # SUMMARY
    # ========================================
    print("\n" + "=" * 70)
    print("✅ TRAINING COMPLETE!")
    print("=" * 70)
    print(f"Model Accuracy: {test_accuracy*100:.2f}%")
    print(f"Model saved to: {model_path}")
    print(f"\nYou can now use this model to make predictions!")
    print("=" * 70)
    
    return model, scaler, test_accuracy


def load_model(model_path='services/model.joblib'):
    """
    Load a trained model from disk.
    
    Args:
        model_path (str): Path to the saved model file
    
    Returns:
        dict: Dictionary containing model, scaler, features, and accuracy
    """
    if not os.path.exists(model_path):
        print(f"❌ Error: Model file not found at {model_path}")
        print(f"   Please train the model first: python services/train_model.py")
        return None
    
    model_data = joblib.load(model_path)
    return model_data


if __name__ == "__main__":
    # Run training when script is executed directly
    train_model()

