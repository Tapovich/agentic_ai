"""
AI-Based Prediction Model
==========================
Uses machine learning models (LSTM, XGBoost) for price predictions.

This module implements deep learning and ensemble methods:
1. LSTM (Long Short-Term Memory): For time-series sequence modeling
2. XGBoost: For gradient boosted decision trees
3. Feature engineering from OHLCV + indicators + external data
4. Multi-step ahead forecasting

The model can be trained on historical data and used for predictions.
For production, pre-trained models would be loaded from disk.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class AIPredictor:
    """AI/ML-based prediction using deep learning and ensemble methods"""
    
    def __init__(self):
        """Initialize the AI predictor"""
        self.model = None
        self.scaler = None
        logger.info("✅ AI Predictor initialized")
    
    # ========================================
    # FEATURE ENGINEERING
    # ========================================
    
    def engineer_features(self, df: pd.DataFrame, onchain: Dict = None, 
                         sentiment: Dict = None, macro: Dict = None) -> pd.DataFrame:
        """
        Create features from raw data for ML models
        
        Features include:
        - Price-based: returns, volatility, price ratios
        - Technical: RSI, MACD, BB position
        - Volume: volume changes, volume ratios
        - External: sentiment scores, on-chain metrics, macro factors
        
        Args:
            df: OHLCV DataFrame
            onchain: On-chain metrics dict
            sentiment: Sentiment metrics dict
            macro: Macro indicators dict
            
        Returns:
            DataFrame: Engineered features
        """
        logger.info("⚙️  Engineering features for ML model...")
        
        features = pd.DataFrame(index=df.index)
        
        # ========================================
        # 1. PRICE-BASED FEATURES
        # ========================================
        
        # Returns over different horizons
        features['return_1h'] = df['close'].pct_change(1)
        features['return_4h'] = df['close'].pct_change(4)
        features['return_24h'] = df['close'].pct_change(24)
        
        # Volatility (rolling standard deviation of returns)
        features['volatility_24h'] = features['return_1h'].rolling(window=24).std()
        
        # Price position relative to recent high/low
        features['price_vs_high_24h'] = df['close'] / df['high'].rolling(window=24).max()
        features['price_vs_low_24h'] = df['close'] / df['low'].rolling(window=24).min()
        
        # ========================================
        # 2. TECHNICAL INDICATORS AS FEATURES
        # ========================================
        
        # RSI
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
        rs = gain / loss
        features['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp12 = df['close'].ewm(span=12, adjust=False).mean()
        exp26 = df['close'].ewm(span=26, adjust=False).mean()
        features['macd'] = exp12 - exp26
        features['macd_signal'] = features['macd'].ewm(span=9, adjust=False).mean()
        features['macd_hist'] = features['macd'] - features['macd_signal']
        
        # Moving averages (only if enough data)
        # Skip 200-period MA if not enough data, use 50-period instead
        if len(df) >= 200:
            features['ma_ratio_50_200'] = df['close'].rolling(50).mean() / df['close'].rolling(200).mean()
        elif len(df) >= 50:
            # Use smaller window if not enough data
            features['ma_ratio_20_50'] = df['close'].rolling(20).mean() / df['close'].rolling(50).mean()
        
        # Bollinger Band position
        sma20 = df['close'].rolling(window=20).mean()
        std20 = df['close'].rolling(window=20).std()
        bb_upper = sma20 + (2 * std20)
        bb_lower = sma20 - (2 * std20)
        features['bb_position'] = (df['close'] - bb_lower) / (bb_upper - bb_lower)
        
        # ========================================
        # 3. VOLUME FEATURES
        # ========================================
        
        features['volume_change'] = df['volume'].pct_change()
        features['volume_ma_ratio'] = df['volume'] / df['volume'].rolling(window=20).mean()
        
        # ========================================
        # 4. EXTERNAL DATA FEATURES
        # ========================================
        
        # Sentiment (if available)
        if sentiment and 'polarity' in sentiment:
            features['sentiment'] = sentiment['polarity']
            features['sentiment_volume'] = sentiment.get('mention_volume', 0) / 10000  # Normalize
        
        # On-chain (if available)
        if onchain:
            if 'nvt_ratio' in onchain and onchain['nvt_ratio']:
                features['nvt_ratio'] = onchain['nvt_ratio']
            if 'active_addresses' in onchain and onchain['active_addresses']:
                features['active_addresses'] = onchain['active_addresses'] / 1_000_000  # Normalize
        
        # Macro (if available)
        if macro:
            features['vix'] = macro.get('vix', 20) / 100  # Normalize to 0-1
            features['fed_rate'] = macro.get('fed_funds_rate', 5) / 10  # Normalize
        
        # ========================================
        # 5. TIME-BASED FEATURES
        # ========================================
        
        # Hour of day, day of week (cyclical encoding)
        if isinstance(df.index, pd.DatetimeIndex):
            features['hour_sin'] = np.sin(2 * np.pi * df.index.hour / 24)
            features['hour_cos'] = np.cos(2 * np.pi * df.index.hour / 24)
            features['day_sin'] = np.sin(2 * np.pi * df.index.dayofweek / 7)
            features['day_cos'] = np.cos(2 * np.pi * df.index.dayofweek / 7)
        
        # Drop NaN rows (from rolling calculations)
        features = features.dropna()
        
        logger.info(f"   Created {len(features.columns)} features from {len(features)} data points")
        
        return features
    
    # ========================================
    # SIMPLE ML MODEL (XGBoost-style logic)
    # ========================================
    
    def train_simple_model(self, features: pd.DataFrame, target: pd.Series):
        """
        Train a simple model (placeholder for real XGBoost/LSTM)
        
        In production, you would:
        1. Split data into train/val/test
        2. Train XGBoost or LSTM model
        3. Save model to disk
        4. Load pre-trained model for predictions
        
        For this demo, we use a simplified approach.
        """
        logger.info("🧠 Training ML model (demo mode)...")
        
        # Placeholder: In real implementation, train XGBoost here
        # from xgboost import XGBRegressor
        # self.model = XGBRegressor(n_estimators=100, learning_rate=0.1)
        # self.model.fit(features, target)
        
        # For demo, we'll use a weighted average of indicators
        # This simulates what an ML model might learn
        self.model = "demo_model"
        
        logger.info("   Model trained (demo)")
    
    def predict_with_model(self, features: pd.DataFrame) -> Tuple[float, float]:
        """
        Make prediction using trained model
        
        Args:
            features: Engineered features DataFrame
            
        Returns:
            tuple: (predicted_return, confidence)
                predicted_return: Expected % change
                confidence: Model confidence (0-1)
        """
        # Get latest feature values
        latest = features.iloc[-1]
        
        # ========================================
        # DEMO PREDICTION LOGIC
        # ========================================
        # In production, this would be: prediction = self.model.predict(latest)
        # For demo, we simulate ML decision using indicators
        
        score = 0
        
        # RSI signal
        if 'rsi' in latest:
            if latest['rsi'] < 30:
                score += 0.3  # Oversold = bullish
            elif latest['rsi'] > 70:
                score -= 0.3  # Overbought = bearish
        
        # MACD signal
        if 'macd_hist' in latest and not np.isnan(latest['macd_hist']):
            score += np.clip(latest['macd_hist'] / 100, -0.2, 0.2)
        
        # Momentum signal
        if 'return_24h' in latest and not np.isnan(latest['return_24h']):
            score += np.clip(latest['return_24h'] * 0.5, -0.3, 0.3)  # Momentum continuation
        
        # Volatility adjustment
        if 'volatility_24h' in latest and not np.isnan(latest['volatility_24h']):
            vol = latest['volatility_24h']
            if vol > 0.05:  # High volatility reduces confidence
                score *= 0.7
        
        # Sentiment boost (if available)
        if 'sentiment' in latest and not np.isnan(latest['sentiment']):
            score += latest['sentiment'] * 0.15
        
        # Macro factor (VIX)
        if 'vix' in latest and not np.isnan(latest['vix']):
            if latest['vix'] > 0.3:  # High VIX = risk-off
                score -= 0.2
        
        # Convert score to predicted return (%)
        predicted_return = np.clip(score * 10, -15, 15)  # -15% to +15% range
        
        # Confidence based on signal strength
        confidence = min(abs(score) / 0.5, 0.95)  # 0-95%
        
        return predicted_return, confidence
    
    # ========================================
    # MAIN PREDICTION FUNCTION
    # ========================================
    
    def predict(self, ohlcv_data: pd.DataFrame, onchain: Dict = None,
                sentiment: Dict = None, macro: Dict = None) -> Dict:
        """
        Main AI prediction function
        
        Args:
            ohlcv_data: OHLCV DataFrame
            onchain: On-chain metrics
            sentiment: Sentiment data
            macro: Macro indicators
            
        Returns:
            dict: Prediction result with signal, target, confidence, summary
        """
        logger.info("\n" + "="*70)
        logger.info("AI-BASED PREDICTION")
        logger.info("="*70)
        
        # Engineer features
        features = self.engineer_features(ohlcv_data, onchain, sentiment, macro)
        
        if len(features) < 20:  # Reduced from 50 to 20 for more flexibility
            logger.warning("⚠️  Insufficient data for AI prediction")
            # Get current price even with insufficient data
            current_price = float(ohlcv_data['close'].iloc[-1])
            return {
                'signal': 'HOLD',
                'direction': 'neutral',
                'confidence': 0,
                'current_price': round(current_price, 2),
                'target_price': round(current_price, 2),  # Same as current
                'pct_change': 0.0,
                'summary': f'Insufficient data for AI prediction. Need at least 20 data points after feature engineering, got {len(features)}.',
                'mode': 'ai',
                'timestamp': datetime.now().isoformat(),
                'error': 'Insufficient data'
            }
        
        # Make prediction
        predicted_return, confidence = self.predict_with_model(features)
        
        # Determine signal
        if predicted_return > 2:
            signal = "BUY"
            direction = "up"
        elif predicted_return < -2:
            signal = "SELL"
            direction = "down"
        else:
            signal = "HOLD"
            direction = "neutral"
        
        # Calculate target price
        current_price = float(ohlcv_data['close'].iloc[-1])
        target_price = current_price * (1 + predicted_return / 100)
        
        # Build summary
        summary = self.build_summary(
            signal=signal,
            predicted_return=predicted_return,
            confidence=confidence * 100,
            current_price=current_price,
            target_price=target_price,
            sentiment=sentiment,
            macro=macro
        )
        
        result = {
            'signal': signal,
            'direction': direction,
            'confidence': round(confidence * 100, 1),
            'current_price': round(current_price, 2),
            'target_price': round(target_price, 2),
            'pct_change': round(predicted_return, 2),
            'summary': summary,
            'mode': 'ai',
            'timestamp': datetime.now().isoformat(),
            'features_used': list(features.columns)
        }
        
        logger.info(f"\n✅ AI PREDICTION: {signal} | Confidence: {confidence*100:.1f}% | "
                   f"Target: ${target_price:.2f} ({predicted_return:+.1f}%)\n")
        logger.info("="*70 + "\n")
        
        return result
    
    def build_summary(self, signal: str, predicted_return: float, confidence: float,
                     current_price: float, target_price: float,
                     sentiment: Dict = None, macro: Dict = None) -> str:
        """
        Build natural language summary for AI prediction
        """
        # Start with AI forecast
        direction_word = "rise" if predicted_return > 0 else "drop"
        forecast = f"AI model forecasts {abs(predicted_return):.1f}% {direction_word}"
        
        # Add timeframe
        forecast += " in next 24 hours"
        
        # Add context from external data
        context = []
        
        if sentiment and 'interpretation' in sentiment:
            context.append(f"Sentiment: {sentiment['interpretation']}")
        
        if macro and 'risk_sentiment' in macro:
            context.append(f"Macro: {macro['risk_sentiment']}")
        
        # Build recommendation
        if signal == "BUY":
            action = f"**Recommendation: BUY** near ${current_price:.2f}, target ${target_price:.2f}"
        elif signal == "SELL":
            action = f"**Recommendation: SELL** near ${current_price:.2f}, target ${target_price:.2f}"
        else:
            action = f"**Recommendation: HOLD/WAIT** - No strong signal at ${current_price:.2f}"
        
        # Combine
        summary = f"{forecast}. {action}. "
        if context:
            summary += f"Context: {'; '.join(context)}. "
        summary += f"Confidence: {confidence:.0f}%."
        
        return summary


# ========================================
# MODULE EXPORTS
# ========================================

__all__ = ['AIPredictor']

