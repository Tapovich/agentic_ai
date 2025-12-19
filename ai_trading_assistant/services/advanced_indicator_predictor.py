"""
Advanced Indicator-Based Prediction Service
============================================
Formula-based prediction using technical indicators and composite scoring.

This module:
1. Fetches OHLCV data from advanced_data_service
2. Computes multiple technical indicators (RSI, MACD, MA, Bollinger Bands, Volume Delta)
3. Builds a composite score from all indicators
4. Generates BUY/SELL/HOLD signals with target prices and time horizons
5. Provides natural language explanations

Author: AI Trading Assistant Team
Created: 2025-11-13
"""

import pandas as pd
from services.advanced_data_service import AdvancedDataService


# ============================================
# INDICATOR CALCULATIONS
# ============================================

def compute_indicators(df: pd.DataFrame) -> dict:
    """
    Compute all technical indicators from OHLCV data
    
    Args:
        df (pd.DataFrame): OHLCV data with columns [open, high, low, close, volume]
        
    Returns:
        dict: Dictionary containing all indicator values
        
    Indicators Explained:
        - RSI (14): Relative Strength Index - measures momentum on 0-100 scale
                    > 70 = overbought (potential sell), < 30 = oversold (potential buy)
        
        - MACD (12,26,9): Moving Average Convergence Divergence - trend indicator
                          MACD > Signal = bullish, MACD < Signal = bearish
        
        - MA50, MA200: Moving Averages - smooth price to show trend
                       MA50 > MA200 = uptrend (golden cross)
                       MA50 < MA200 = downtrend (death cross)
        
        - Bollinger Bands: Volatility indicator with upper/lower bounds
                           Price at upper = overbought, at lower = oversold
        
        - Volume Delta: Change in trading volume
                        Positive = increasing interest, Negative = decreasing interest
    """
    prices = df['close']
    
    # ========================================
    # 1. RSI (Relative Strength Index)
    # ========================================
    # Measures momentum - how fast price is moving up or down
    # RSI > 70: Market is overbought (too many buyers, might reverse down)
    # RSI < 30: Market is oversold (too many sellers, might reverse up)
    
    delta = prices.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    rsi_value = float(rsi.iloc[-1]) if len(rsi) > 0 else 50.0
    
    # ========================================
    # 2. MACD (Moving Average Convergence Divergence)
    # ========================================
    # Shows trend changes and momentum
    # When MACD line crosses above signal line = buy signal
    # When MACD line crosses below signal line = sell signal
    
    ema12 = prices.ewm(span=12, adjust=False).mean()
    ema26 = prices.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    
    macd_value = float(macd_line.iloc[-1])
    macd_signal = float(signal_line.iloc[-1])
    
    # ========================================
    # 3. EMAs (Exponential Moving Averages)
    # ========================================
    # TASK 40: Replaced SMA with EMA - responds faster to price changes
    # EMA gives more weight to recent prices vs SMA which treats all equally
    # Better for volatile markets like crypto
    #
    # EMA 9: Very short-term trend (scalping, day trading)
    # EMA 20: Short-term trend
    # EMA 50: Medium-term trend
    # EMA 200: Major trend line (bull/bear market indicator)
    #
    # Price above EMA = uptrend, below EMA = downtrend
    # EMA50 > EMA200 = "Golden Cross" (bullish)
    # EMA50 < EMA200 = "Death Cross" (bearish)
    
    ema9 = float(prices.ewm(span=9, adjust=False).mean().iloc[-1])
    ema20 = float(prices.ewm(span=20, adjust=False).mean().iloc[-1])
    ema50 = float(prices.ewm(span=50, adjust=False).mean().iloc[-1])
    
    # EMA200 needs at least 200 data points
    if len(prices) >= 200:
        ema200 = float(prices.ewm(span=200, adjust=False).mean().iloc[-1])
    else:
        ema200 = ema50  # Fallback if not enough data
    
    # ========================================
    # 4. Bollinger Bands (using EMA 20)
    # ========================================
    # TASK 40: Updated to use EMA instead of SMA for faster response
    # Shows volatility and potential reversal points
    # Upper band = resistance level, Lower band = support level
    # Price touching upper band = overbought
    # Price touching lower band = oversold
    
    ema20_series = prices.ewm(span=20, adjust=False).mean()
    std20 = prices.rolling(window=20).std()
    
    bb_upper = float((ema20_series + (2 * std20)).iloc[-1])
    bb_lower = float((ema20_series - (2 * std20)).iloc[-1])
    bb_middle = float(ema20_series.iloc[-1])
    
    # ========================================
    # 5. Volume Delta
    # ========================================
    # Change in trading volume from previous period
    # Positive = more trading activity (interest increasing)
    # Negative = less trading activity (interest decreasing)
    # High volume with price move = strong signal (confirmed)
    # Low volume with price move = weak signal (might reverse)
    
    if 'volume' in df.columns and len(df) >= 2:
        current_volume = float(df['volume'].iloc[-1])
        previous_volume = float(df['volume'].iloc[-2])
        volume_delta = current_volume - previous_volume
    else:
        volume_delta = 0.0
    
    # Get current price
    current_price = float(prices.iloc[-1])
    
    # Return all indicators as a dictionary (TASK 40: EMAs instead of SMAs)
    return {
        'rsi': rsi_value,
        'macd': macd_value,
        'macd_signal': macd_signal,
        'ema9': ema9,
        'ema20': ema20,
        'ema50': ema50,
        'ema200': ema200,
        'bb_upper': bb_upper,
        'bb_middle': bb_middle,
        'bb_lower': bb_lower,
        'volume_delta': volume_delta,
        'current_price': current_price
    }


# ============================================
# SIGNAL GENERATION
# ============================================

def build_indicator_signal(indicators: dict, current_price: float) -> dict:
    """
    Build trading signal from indicator composite score
    
    Args:
        indicators (dict): Computed indicators from compute_indicators()
        current_price (float): Current market price
        
    Returns:
        dict: Trading signal with target price, confidence, and timing
        
    Scoring System Explained:
        We score each category from -1 to +1 (or -2 to +2 for momentum/trend)
        Then sum all scores to get total_score
        
        Momentum Score (RSI + MACD):
            - Checks if market is overbought/oversold
            - Checks if momentum is bullish/bearish
            
        Trend Score (MA50 vs MA200):
            - Checks if in uptrend or downtrend
            
        Volume Score:
            - Checks if trading activity is increasing/decreasing
        
        Final Signal:
            total_score >= 2  → BUY  (bullish signals dominate)
            total_score <= -2 → SELL (bearish signals dominate)
            otherwise        → HOLD (mixed signals, wait for clarity)
    """
    
    # ========================================
    # Step 1: Calculate Momentum Score
    # ========================================
    momentum_score = 0
    
    # RSI Component
    # RSI > 70 means overbought (too high, might drop) → bearish (-1)
    # RSI < 30 means oversold (too low, might rise) → bullish (+1)
    if indicators['rsi'] > 70:
        momentum_score -= 1
        rsi_signal = "Overbought (RSI > 70)"
    elif indicators['rsi'] < 30:
        momentum_score += 1
        rsi_signal = "Oversold (RSI < 30)"
    else:
        rsi_signal = f"Neutral (RSI = {indicators['rsi']:.1f})"
    
    # MACD Component
    # MACD > Signal means upward momentum → bullish (+1)
    # MACD < Signal means downward momentum → bearish (-1)
    if indicators['macd'] > indicators['macd_signal']:
        momentum_score += 1
        macd_signal = "Bullish (MACD > Signal)"
    else:
        momentum_score -= 1
        macd_signal = "Bearish (MACD < Signal)"
    
    # ========================================
    # Step 2: Calculate Trend Score (TASK 40: Using EMAs)
    # ========================================
    trend_score = 0
    
    # EMA alignment scoring - stronger signals than simple MA crossover
    # EMAs react faster to price changes, better for crypto volatility
    
    # Check EMA 9 > 20 > 50 (strong uptrend alignment)
    if indicators['ema9'] > indicators['ema20'] > indicators['ema50']:
        trend_score += 2  # Strong uptrend
        trend_signal = "Strong Uptrend (EMA 9>20>50)"
    elif indicators['ema9'] > indicators['ema20']:
        trend_score += 1  # Bullish
        trend_signal = "Bullish (EMA 9>20)"
    elif indicators['ema9'] < indicators['ema20'] < indicators['ema50']:
        trend_score -= 2  # Strong downtrend
        trend_signal = "Strong Downtrend (EMA 9<20<50)"
    elif indicators['ema9'] < indicators['ema20']:
        trend_score -= 1  # Bearish
        trend_signal = "Bearish (EMA 9<20)"
    else:
        trend_score += 0  # Neutral
        trend_signal = "Sideways (EMAs mixed)"
    
    # Long-term trend: EMA50 > EMA200 = bull market
    if indicators['ema50'] > indicators['ema200']:
        trend_score += 1
        longterm_signal = "Bull Market (EMA50>200)"
    else:
        trend_score -= 1
        longterm_signal = "Bear Market (EMA50<200)"
    
    # ========================================
    # Step 3: Calculate Volume Score
    # ========================================
    volume_score = 0
    
    # Positive volume delta means increasing activity → bullish (+1)
    # Negative volume delta means decreasing activity → bearish (-1)
    if indicators['volume_delta'] > 0:
        volume_score += 1
        volume_signal = "Increasing volume"
    else:
        volume_score -= 1
        volume_signal = "Decreasing volume"
    
    # ========================================
    # Step 4: Calculate Total Score
    # ========================================
    # Sum all scores (TASK 40: Updated for EMA-based scoring)
    # momentum (-2 to +2) + trend (-3 to +3) + volume (-1 to +1)
    # Total range: -6 to +6
    total_score = momentum_score + trend_score + volume_score
    
    # ========================================
    # Step 5: Determine Signal
    # ========================================
    # Map total score to BUY/SELL/HOLD (updated thresholds for wider range)
    if total_score >= 3:
        signal = "BUY"
    elif total_score <= -3:
        signal = "SELL"
    else:
        signal = "HOLD"
    
    # ========================================
    # Step 6: Calculate Target Price
    # ========================================
    # Based on signal, estimate how much price might move
    
    if signal == "BUY":
        # Bullish: expect 3% to 7% upside
        # More confident (higher score) = larger target
        target_pct = 3 + (abs(total_score) * 1.0)  # 3% base + score bonus
        target_pct = min(target_pct, 7)  # Cap at 7%
        
    elif signal == "SELL":
        # Bearish: expect 3% to 7% downside
        target_pct = -(3 + (abs(total_score) * 1.0))
        target_pct = max(target_pct, -7)  # Cap at -7%
        
    else:  # HOLD
        # No clear direction: expect sideways movement
        target_pct = 0
    
    target_price = current_price * (1 + target_pct / 100)
    
    # ========================================
    # Step 7: Calculate Confidence
    # ========================================
    # Confidence based on score strength
    # Score of 3 or 4 = high confidence (~100%)
    # Score of 2 = moderate confidence (~67%)
    # Score of 1 or 0 = low confidence (~33%)
    confidence = min(abs(total_score) / 3 * 100, 99)
    
    # ========================================
    # Step 8: Determine Time Horizon
    # ========================================
    # How long until target might be reached
    # Strong signals = faster move
    # Weak signals = slower move
    if abs(total_score) >= 3:
        horizon = "next 4-12 hours"
    elif abs(total_score) >= 2:
        horizon = "next 12-24 hours"
    else:
        horizon = "next 1-2 days"
    
    # ========================================
    # Step 9: Build Natural Language Summary
    # ========================================
    # Create human-readable explanation
    
    summary_parts = []
    
    # Start with RSI condition if notable
    if indicators['rsi'] > 70:
        summary_parts.append(f"Market is overbought (RSI {indicators['rsi']:.1f} > 70)")
    elif indicators['rsi'] < 30:
        summary_parts.append(f"Market is oversold (RSI {indicators['rsi']:.1f} < 30)")
    else:
        summary_parts.append(f"Market momentum is neutral (RSI {indicators['rsi']:.1f})")
    
    # Add composite score
    summary_parts.append(f"Composite score = {total_score:+d}")
    
    # Add recommendation
    if signal == "BUY":
        summary_parts.append(f"Suggestion: BUY in {horizon} towards ${target_price:.2f} (+{target_pct:.1f}%)")
    elif signal == "SELL":
        summary_parts.append(f"Suggestion: SELL in {horizon} towards ${target_price:.2f} ({target_pct:.1f}%)")
    else:
        summary_parts.append(f"Suggestion: HOLD - wait for clearer signals")
    
    # Add confidence
    summary_parts.append(f"Confidence ~{confidence:.0f}%")
    
    summary = ". ".join(summary_parts) + "."
    
    # Return complete signal dict
    return {
        'signal': signal,
        'target_price': round(target_price, 2),
        'expected_change_pct': round(target_pct, 2),
        'confidence': round(confidence, 1),
        'horizon': horizon,
        'total_score': total_score,
        'score_breakdown': {
            'momentum': momentum_score,
            'trend': trend_score,
            'volume': volume_score
        },
        'signal_reasons': {
            'rsi': rsi_signal,
            'macd': macd_signal,
            'trend': trend_signal,
            'volume': volume_signal
        },
        'summary': summary
    }


# ============================================
# MAIN PREDICTION FUNCTION
# ============================================

def advanced_indicator_predict(symbol: str, timeframe: str = "1h") -> dict:
    """
    Main function to run advanced indicator-based prediction
    
    Args:
        symbol (str): Trading pair (e.g., 'BTC/USDT')
        timeframe (str): Candle interval ('1h', '4h', '1d')
        
    Returns:
        dict: Complete prediction result with signal, target, confidence, and chart data
        
    Example Usage:
        >>> result = advanced_indicator_predict('BTC/USDT', '1h')
        >>> print(f"Signal: {result['signal']}")
        >>> print(f"Target: ${result['target_price']}")
        >>> print(f"Confidence: {result['confidence']}%")
        >>> print(f"Summary: {result['summary']}")
        
    Output Structure:
        {
            'mode': 'indicator',
            'symbol': 'BTC/USDT',
            'timeframe': '1h',
            'signal': 'BUY',  # or 'SELL', 'HOLD'
            'target_price': 99500.00,
            'expected_change_pct': 1.5,
            'confidence': 78.5,
            'horizon': 'next 4-12 hours',
            'indicators': {...},  # all raw indicator values
            'summary': '...',  # natural language explanation
            'chart': {
                'timestamps': [...],
                'prices': [...],
                'prediction': [...]  # target price at last point
            }
        }
    """
    
    print(f"\n{'='*70}")
    print(f"ADVANCED INDICATOR PREDICTION")
    print(f"{'='*70}")
    print(f"Symbol: {symbol}")
    print(f"Timeframe: {timeframe}")
    print(f"{'='*70}\n")
    
    # ========================================
    # Step 1: Fetch Price Data
    # ========================================
    print(f"[1/5] Fetching price data...")
    
    # Get OHLCV data using UNIFIED SOURCE (TASK 47 - ensures consistency)
    from services.unified_data_service import get_price_history_df, validate_df_for_indicators
    
    # Use unified data service for consistency across all analytics
    df = get_price_history_df(symbol.replace("/", ""), timeframe, limit=300)
    
    # Validate sufficient data
    is_valid, error_msg = validate_df_for_indicators(df, min_candles=50)
    if not is_valid:
        # Not enough data for calculations
        return {
            'mode': 'indicator',
            'symbol': symbol,
            'timeframe': timeframe,
            'signal': 'HOLD',
            'error': f'Insufficient data: {error_msg}',
            'summary': f'Cannot compute prediction - {error_msg}. Try syncing price history.'
        }
    
    print(f"   ✅ Fetched {len(df)} candles")
    
    # ========================================
    # Step 2: Compute Indicators
    # ========================================
    print(f"[2/5] Computing technical indicators...")
    
    indicators = compute_indicators(df)
    
    print(f"   ✅ RSI: {indicators['rsi']:.1f}")
    print(f"   ✅ MACD: {indicators['macd']:.2f} vs Signal: {indicators['macd_signal']:.2f}")
    print(f"   ✅ EMA9: ${indicators['ema9']:.2f}, EMA20: ${indicators['ema20']:.2f}")
    print(f"   ✅ EMA50: ${indicators['ema50']:.2f}, EMA200: ${indicators['ema200']:.2f}")
    print(f"   ✅ Volume Delta: {indicators['volume_delta']:,.0f}")
    
    # ========================================
    # Step 3: Generate Signal
    # ========================================
    print(f"[3/5] Generating trading signal...")
    
    current_price = indicators['current_price']
    signal_result = build_indicator_signal(indicators, current_price)
    
    print(f"   ✅ Signal: {signal_result['signal']}")
    print(f"   ✅ Target: ${signal_result['target_price']:.2f} ({signal_result['expected_change_pct']:+.1f}%)")
    print(f"   ✅ Confidence: {signal_result['confidence']:.1f}%")
    
    # ========================================
    # Step 4: Prepare Chart Data (TASK 41: with EMAs)
    # ========================================
    print(f"[4/5] Preparing chart data...")
    
    # Get last 50 candles for chart
    chart_df = df.tail(50)
    
    # Calculate EMAs for chart (TASK 40/41)
    chart_df['ema9'] = chart_df['close'].ewm(span=9, adjust=False).mean()
    chart_df['ema20'] = chart_df['close'].ewm(span=20, adjust=False).mean()
    chart_df['ema50'] = chart_df['close'].ewm(span=50, adjust=False).mean()
    
    # EMA 100 and 200 need more data, use from original df
    if len(df) >= 100:
        chart_df['ema100'] = df['close'].ewm(span=100, adjust=False).mean().tail(50)
    else:
        chart_df['ema100'] = chart_df['ema50']  # Fallback
    
    if len(df) >= 200:
        chart_df['ema200'] = df['close'].ewm(span=200, adjust=False).mean().tail(50)
    else:
        chart_df['ema200'] = chart_df['ema50']  # Fallback
    
    # Extract timestamps and prices
    timestamps = [ts.isoformat() for ts in chart_df.index]
    prices = [float(p) for p in chart_df['close'].values]
    
    # Extract EMA series for chart overlay (TASK 41)
    ema9_series = [float(v) if not pd.isna(v) else None for v in chart_df['ema9'].values]
    ema20_series = [float(v) if not pd.isna(v) else None for v in chart_df['ema20'].values]
    ema50_series = [float(v) if not pd.isna(v) else None for v in chart_df['ema50'].values]
    ema100_series = [float(v) if not pd.isna(v) else None for v in chart_df['ema100'].values]
    ema200_series = [float(v) if not pd.isna(v) else None for v in chart_df['ema200'].values]
    
    # Create prediction line (None for historical, target for future)
    # This shows where we expect price to go
    prediction_line = [None] * len(prices)
    prediction_line.append(signal_result['target_price'])  # Add target at end
    
    # Add future timestamp for prediction point
    from datetime import timedelta
    future_timestamp = chart_df.index[-1] + timedelta(hours=24)
    timestamps.append(future_timestamp.isoformat())
    
    # Extend EMA series with None for future point (to match length)
    ema9_series.append(None)
    ema20_series.append(None)
    ema50_series.append(None)
    ema100_series.append(None)
    ema200_series.append(None)
    
    print(f"   ✅ Chart prepared with {len(timestamps)} data points + EMAs")
    
    # ========================================
    # Step 5: Build Final Result
    # ========================================
    print(f"[5/5] Building final result...")
    
    result = {
        'mode': 'indicator',
        'symbol': symbol,
        'timeframe': timeframe,
        'signal': signal_result['signal'],
        'target_price': signal_result['target_price'],
        'expected_change_pct': signal_result['expected_change_pct'],
        'confidence': signal_result['confidence'],
        'horizon': signal_result['horizon'],
        'current_price': current_price,
        'total_score': signal_result['total_score'],
        'score_breakdown': signal_result['score_breakdown'],
        'signal_reasons': signal_result['signal_reasons'],
        'indicators': indicators,
        'summary': signal_result['summary'],
        'chart': {
            'timestamps': timestamps,
            'prices': prices,
            'prediction': prediction_line,
            # TASK 41: EMA overlays for chart visualization
            'ema9': ema9_series,
            'ema20': ema20_series,
            'ema50': ema50_series,
            'ema100': ema100_series,
            'ema200': ema200_series
        }
    }
    
    print(f"\n{'='*70}")
    print(f"✅ PREDICTION COMPLETE")
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
        result (dict): Result from advanced_indicator_predict()
    """
    print(f"\n{'='*70}")
    print(f"PREDICTION SUMMARY")
    print(f"{'='*70}")
    print(f"Symbol: {result['symbol']}")
    print(f"Timeframe: {result['timeframe']}")
    print(f"")
    print(f"📊 SIGNAL: {result['signal']}")
    print(f"💰 Current Price: ${result['current_price']:.2f}")
    print(f"🎯 Target Price: ${result['target_price']:.2f}")
    print(f"📈 Expected Change: {result['expected_change_pct']:+.1f}%")
    print(f"✅ Confidence: {result['confidence']:.1f}%")
    print(f"⏰ Time Horizon: {result['horizon']}")
    print(f"")
    print(f"📝 SUMMARY:")
    print(f"{result['summary']}")
    print(f"{'='*70}\n")


# ============================================
# EXAMPLE USAGE
# ============================================

if __name__ == "__main__":
    """
    Test the advanced indicator predictor
    
    Run this file directly to test:
        python services/advanced_indicator_predictor.py
    """
    
    # Example 1: Bitcoin 1-hour
    print("\n🔮 Testing Bitcoin (BTC/USDT) - 1 hour timeframe\n")
    btc_result = advanced_indicator_predict('BTC/USDT', '1h')
    print_prediction_summary(btc_result)
    
    # Example 2: Ethereum 4-hour
    print("\n🔮 Testing Ethereum (ETH/USDT) - 4 hour timeframe\n")
    eth_result = advanced_indicator_predict('ETH/USDT', '4h')
    print_prediction_summary(eth_result)
    
    print("\n✅ All tests complete!")

