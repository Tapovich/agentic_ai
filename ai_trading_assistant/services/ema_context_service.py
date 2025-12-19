"""
EMA Context Service (TASK 43)
==============================
Provides EMA trend context for bot execution decisions.

This service helps bots understand the current market trend:
- Grid bots prefer sideways markets (no strong trend)
- DCA bots prefer trending markets (matching their side)

By making bots "trend-aware", we improve execution timing
and avoid trading against strong trends.

Educational Purpose:
This demonstrates how professional trading bots adapt to
market conditions rather than blindly executing trades.

Author: AI Trading Assistant Team
Created: 2025-11-13
"""

import pandas as pd
from services.advanced_data_service import AdvancedDataService
from services.indicator_service import get_ema_signals


def get_latest_ema_context(symbol: str, timeframe: str = "1h", limit: int = 300) -> dict:
    """
    Get current EMA trend context for a symbol (TASK 43).
    
    This function fetches recent price data and analyzes EMA signals
    to determine the current market trend. Bots use this to decide
    whether to execute trades or wait for better conditions.
    
    Args:
        symbol (str): Trading symbol (e.g., "BTCUSDT")
        timeframe (str): Candle timeframe (e.g., "1h", "4h", "1d")
        limit (int): Number of candles to fetch (default 300 for EMA 200)
    
    Returns:
        dict: EMA signal context with:
            - trend_label: 'long_term_uptrend' or 'long_term_downtrend'
            - overall_signal: 'BUY', 'SELL', or 'HOLD'
            - confidence: 0-100
            - golden_cross: bool
            - death_cross: bool
            - short_term: 'bullish' or 'bearish'
            - explanation: str
            - success: bool (True if data available)
            - error: str (if failed)
    
    Example:
        context = get_latest_ema_context("BTCUSDT", "1h")
        if context['success']:
            if context['overall_signal'] == 'BUY':
                print(f"Market is bullish with {context['confidence']}% confidence")
    
    Use Cases:
        Grid Bot: Check if trend is sideways/neutral
        DCA Bot: Check if trend matches bot side (BUY/SELL)
        Portfolio: Assess overall market conditions
    """
    try:
        print(f"📊 Fetching EMA context for {symbol} ({timeframe})...")
        
        # ========================================
        # Step 1: Fetch Price History
        # ========================================
        data_service = AdvancedDataService()
        df = data_service.get_ohlcv(symbol, timeframe, limit)
        
        if df is None or len(df) < 200:
            print(f"⚠️  Insufficient data for {symbol} (need 200, got {len(df) if df is not None else 0})")
            return {
                'success': False,
                'error': 'Insufficient price history',
                'trend_label': 'unknown',
                'overall_signal': 'HOLD',
                'confidence': 0
            }
        
        # ========================================
        # Step 2: Calculate EMAs
        # ========================================
        # EMA calculations need to be done on the dataframe
        df['ema9'] = df['close'].ewm(span=9, adjust=False).mean()
        df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
        df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
        df['ema200'] = df['close'].ewm(span=200, adjust=False).mean()
        
        # ========================================
        # Step 3: Get EMA Signals
        # ========================================
        signals = get_ema_signals(df)
        signals['success'] = True
        
        print(f"✅ EMA Context: {signals['overall_signal']} ({signals['confidence']}% confidence)")
        print(f"   Trend: {signals['trend_label']}")
        print(f"   Short-term: {signals['short_term']}")
        
        if signals['golden_cross']:
            print(f"   🌟 Golden Cross detected!")
        elif signals['death_cross']:
            print(f"   💀 Death Cross detected!")
        
        return signals
        
    except Exception as e:
        print(f"❌ Error getting EMA context for {symbol}: {e}")
        return {
            'success': False,
            'error': str(e),
            'trend_label': 'unknown',
            'overall_signal': 'HOLD',
            'confidence': 0
        }


def should_grid_bot_execute(ema_context: dict) -> tuple[bool, str]:
    """
    Determine if a Grid Bot should execute based on EMA trend (TASK 43).
    
    Grid bots work best in sideways/range-bound markets.
    They should pause when there's a strong uptrend or downtrend.
    
    Args:
        ema_context: EMA signal context from get_latest_ema_context()
    
    Returns:
        tuple: (should_execute: bool, reason: str)
    
    Logic:
        - Execute if: HOLD signal (conflicting/sideways)
        - Execute if: Confidence < 60% (weak trend)
        - Pause if: Strong BUY/SELL with high confidence
        - Pause if: Golden/Death cross (major trend change)
    
    Example:
        context = get_latest_ema_context("BTCUSDT")
        should_run, reason = should_grid_bot_execute(context)
        if not should_run:
            print(f"Grid bot paused: {reason}")
    """
    if not ema_context.get('success'):
        # If we can't get EMA data, allow execution (fail-safe)
        return True, "EMA data unavailable, executing normally"
    
    signal = ema_context.get('overall_signal', 'HOLD')
    confidence = ema_context.get('confidence', 0)
    trend = ema_context.get('trend_label', 'unknown')
    
    # Grid bots prefer sideways markets (HOLD signal)
    if signal == 'HOLD':
        return True, "Market sideways - ideal for grid trading"
    
    # Allow if confidence is low (weak trend, likely to reverse)
    if confidence < 60:
        return True, f"Weak {signal} signal ({confidence}%), grid can execute"
    
    # Pause on Golden/Death cross (major trend change incoming)
    if ema_context.get('golden_cross'):
        return False, "🌟 Golden Cross - strong uptrend expected, grid bot paused"
    
    if ema_context.get('death_cross'):
        return False, "💀 Death Cross - strong downtrend expected, grid bot paused"
    
    # Pause on strong trending signals
    if signal == 'BUY' and confidence >= 60:
        return False, f"Strong uptrend ({confidence}% confidence) - better for DCA BUY, grid bot paused"
    
    if signal == 'SELL' and confidence >= 60:
        return False, f"Strong downtrend ({confidence}% confidence) - better for DCA SELL, grid bot paused"
    
    # Default: allow execution
    return True, "Market conditions acceptable for grid trading"


def should_dca_bot_execute(ema_context: dict, bot_side: str) -> tuple[bool, str]:
    """
    Determine if a DCA Bot should execute based on EMA trend (TASK 43).
    
    DCA bots work best in trending markets that match their direction:
    - DCA BUY: Wants long-term uptrend
    - DCA SELL: Wants long-term downtrend
    
    Args:
        ema_context: EMA signal context from get_latest_ema_context()
        bot_side: 'BUY' or 'SELL'
    
    Returns:
        tuple: (should_execute: bool, reason: str)
    
    Logic:
        DCA BUY:
        - Execute if: long_term_uptrend
        - Execute if: Golden Cross detected
        - Pause if: long_term_downtrend or Death Cross
        
        DCA SELL:
        - Execute if: long_term_downtrend
        - Execute if: Death Cross detected
        - Pause if: long_term_uptrend or Golden Cross
    
    Example:
        context = get_latest_ema_context("BTCUSDT")
        should_run, reason = should_dca_bot_execute(context, "BUY")
        if should_run:
            print(f"DCA BUY approved: {reason}")
    """
    if not ema_context.get('success'):
        # If we can't get EMA data, allow execution (fail-safe)
        return True, "EMA data unavailable, executing normally"
    
    trend = ema_context.get('trend_label', 'unknown')
    signal = ema_context.get('overall_signal', 'HOLD')
    confidence = ema_context.get('confidence', 0)
    
    # ========================================
    # DCA BUY Logic
    # ========================================
    if bot_side == 'BUY':
        # Golden Cross is very bullish - perfect for DCA BUY
        if ema_context.get('golden_cross'):
            return True, "🌟 Golden Cross - excellent timing for DCA BUY"
        
        # Long-term uptrend is ideal
        if trend == 'long_term_uptrend':
            return True, f"Long-term uptrend - ideal for DCA BUY ({confidence}% confidence)"
        
        # Death Cross is very bearish - pause DCA BUY
        if ema_context.get('death_cross'):
            return False, "💀 Death Cross - bad timing for DCA BUY, cycle skipped"
        
        # Long-term downtrend - pause DCA BUY
        if trend == 'long_term_downtrend':
            return False, f"Long-term downtrend - not ideal for DCA BUY, cycle skipped"
        
        # Sideways/uncertain - allow with caution
        return True, "Neutral trend - DCA BUY can proceed with caution"
    
    # ========================================
    # DCA SELL Logic
    # ========================================
    elif bot_side == 'SELL':
        # Death Cross is very bearish - perfect for DCA SELL
        if ema_context.get('death_cross'):
            return True, "💀 Death Cross - excellent timing for DCA SELL"
        
        # Long-term downtrend is ideal
        if trend == 'long_term_downtrend':
            return True, f"Long-term downtrend - ideal for DCA SELL ({confidence}% confidence)"
        
        # Golden Cross is very bullish - pause DCA SELL
        if ema_context.get('golden_cross'):
            return False, "🌟 Golden Cross - bad timing for DCA SELL, cycle skipped"
        
        # Long-term uptrend - pause DCA SELL
        if trend == 'long_term_uptrend':
            return False, f"Long-term uptrend - not ideal for DCA SELL, cycle skipped"
        
        # Sideways/uncertain - allow with caution
        return True, "Neutral trend - DCA SELL can proceed with caution"
    
    else:
        # Unknown side, allow execution
        return True, f"Unknown bot side '{bot_side}', executing normally"


def format_ema_context_summary(ema_context: dict) -> str:
    """
    Format EMA context into a human-readable summary.
    
    Args:
        ema_context: EMA signal context
    
    Returns:
        str: Formatted summary
    
    Example:
        summary = format_ema_context_summary(context)
        print(summary)
        # Output: "BUY signal (75% confidence) | Long-term uptrend | Short-term bullish"
    """
    if not ema_context.get('success'):
        return "EMA data unavailable"
    
    parts = []
    
    # Overall signal
    signal = ema_context.get('overall_signal', 'HOLD')
    confidence = ema_context.get('confidence', 0)
    parts.append(f"{signal} signal ({confidence}% confidence)")
    
    # Trend
    trend = ema_context.get('trend_label', 'unknown')
    if trend == 'long_term_uptrend':
        parts.append("Long-term uptrend")
    elif trend == 'long_term_downtrend':
        parts.append("Long-term downtrend")
    else:
        parts.append("Neutral trend")
    
    # Short-term
    short_term = ema_context.get('short_term', 'unknown')
    if short_term == 'bullish':
        parts.append("Short-term bullish")
    elif short_term == 'bearish':
        parts.append("Short-term bearish")
    
    # Special crosses
    if ema_context.get('golden_cross'):
        parts.append("🌟 Golden Cross")
    elif ema_context.get('death_cross'):
        parts.append("💀 Death Cross")
    
    return " | ".join(parts)

