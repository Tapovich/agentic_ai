"""
Advanced Prediction Model
==========================
Database operations for advanced predictions

This module handles:
- Saving predictions to database
- Retrieving prediction history
- Tracking prediction accuracy
- Performance analytics
"""

from models import db
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)


def save_prediction(user_id: int, symbol: str, mode: str, timeframe: str, result: dict):
    """
    Save a prediction to the database
    
    Args:
        user_id: User ID
        symbol: Trading pair (e.g., 'BTC/USDT')
        mode: Prediction mode ('ai' or 'indicator')
        timeframe: Timeframe ('1h', '4h', '1d')
        result: Prediction result dict
        
    Returns:
        int: Prediction ID or None if failed
    """
    try:
        # Extract values from result
        signal = result.get('signal', 'HOLD')
        direction = result.get('direction', 'neutral')
        confidence = result.get('confidence', 0)
        current_price = result.get('current_price', 0)
        target_price = result.get('target_price', 0)
        pct_change = result.get('pct_change', 0)
        summary = result.get('summary', '')
        
        # Serialize indicators to JSON
        indicators_json = json.dumps(result.get('indicators', {}))
        
        # Calculate target time for evaluation (24h from now for simplicity)
        target_time = datetime.utcnow() + timedelta(hours=24)
        
        # Insert into database
        query = """
            INSERT INTO advanced_predictions 
            (user_id, symbol, mode, timeframe, signal, direction, confidence,
             current_price, target_price, pct_change, summary, indicators_snapshot,
             target_time, outcome)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
        """
        
        prediction_id = db.execute_query(
            query,
            (user_id, symbol, mode, timeframe, signal, direction, confidence,
             current_price, target_price, pct_change, summary, indicators_json,
             target_time.isoformat())
        )
        
        logger.info(f"✅ Saved prediction #{prediction_id}: {signal} {symbol} ({mode} mode)")
        return prediction_id
        
    except Exception as e:
        logger.error(f"❌ Error saving prediction: {e}")
        return None


def get_user_predictions(user_id: int, limit: int = 20):
    """
    Get user's recent predictions
    
    Args:
        user_id: User ID
        limit: Number of predictions to return
        
    Returns:
        list: List of prediction dicts
    """
    try:
        query = """
            SELECT id, symbol, mode, timeframe, signal, confidence,
                   current_price, target_price, pct_change, summary,
                   created_at, outcome, actual_price
            FROM advanced_predictions
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """
        
        rows = db.fetch_all(query, (user_id, limit))
        
        predictions = []
        for row in rows:
            predictions.append({
                'id': row['id'],
                'symbol': row['symbol'],
                'mode': row['mode'],
                'timeframe': row['timeframe'],
                'signal': row['signal'],
                'confidence': float(row['confidence']) if row['confidence'] else 0,
                'current_price': float(row['current_price']) if row['current_price'] else 0,
                'target_price': float(row['target_price']) if row['target_price'] else 0,
                'pct_change': float(row['pct_change']) if row['pct_change'] else 0,
                'summary': row['summary'],
                'created_at': row['created_at'],
                'outcome': row['outcome'],
                'actual_price': float(row['actual_price']) if row['actual_price'] else None
            })
        
        return predictions
        
    except Exception as e:
        logger.error(f"❌ Error fetching predictions: {e}")
        return []


def get_prediction_performance(user_id: int):
    """
    Get prediction performance statistics for a user
    
    Args:
        user_id: User ID
        
    Returns:
        dict: Performance metrics
    """
    try:
        query = """
            SELECT 
                mode,
                COUNT(*) as total,
                SUM(CASE WHEN outcome = 'correct' THEN 1 ELSE 0 END) as correct,
                AVG(confidence) as avg_confidence
            FROM advanced_predictions
            WHERE user_id = ? AND outcome IN ('correct', 'incorrect')
            GROUP BY mode
        """
        
        rows = db.fetch_all(query, (user_id,))
        
        performance = {}
        for row in rows:
            accuracy = (row['correct'] / row['total'] * 100) if row['total'] > 0 else 0
            performance[row['mode']] = {
                'total_predictions': row['total'],
                'correct_predictions': row['correct'],
                'accuracy_pct': round(accuracy, 1),
                'avg_confidence': round(float(row['avg_confidence']), 1) if row['avg_confidence'] else 0
            }
        
        return performance
        
    except Exception as e:
        logger.error(f"❌ Error fetching performance: {e}")
        return {}


def update_prediction_outcome(prediction_id: int, actual_price: float):
    """
    Update a prediction with actual outcome
    
    This should be called periodically to check if predictions
    came true and calculate accuracy.
    
    Args:
        prediction_id: Prediction ID
        actual_price: Actual price at target time
        
    Returns:
        bool: Success status
    """
    try:
        # Get original prediction
        query = "SELECT signal, target_price, current_price FROM advanced_predictions WHERE id = ?"
        pred = db.fetch_one(query, (prediction_id,))
        
        if not pred:
            return False
        
        # Determine if prediction was correct
        signal = pred['signal']
        target = float(pred['target_price'])
        current = float(pred['current_price'])
        
        outcome = 'incorrect'
        
        if signal == 'BUY' and actual_price > current:
            outcome = 'correct'
        elif signal == 'SELL' and actual_price < current:
            outcome = 'correct'
        elif signal == 'HOLD' and abs(actual_price - current) / current < 0.02:  # Within 2%
            outcome = 'correct'
        
        # Calculate accuracy score (how close to target)
        if target > 0:
            accuracy_score = max(0, 100 - abs((actual_price - target) / target * 100))
        else:
            accuracy_score = 0
        
        # Update database
        update_query = """
            UPDATE advanced_predictions
            SET actual_price = ?, outcome = ?, accuracy_score = ?
            WHERE id = ?
        """
        
        db.execute_query(update_query, (actual_price, outcome, accuracy_score, prediction_id))
        
        logger.info(f"✅ Updated prediction #{prediction_id}: {outcome}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error updating prediction outcome: {e}")
        return False


# ========================================
# MODULE EXPORTS
# ========================================

__all__ = [
    'save_prediction',
    'get_user_predictions',
    'get_prediction_performance',
    'update_prediction_outcome'
]

