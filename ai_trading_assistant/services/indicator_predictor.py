"""
Indicator-Based Prediction Model
=================================
Uses technical indicators and formula-based rules to predict price movements.

This module implements a systematic, rule-based approach similar to
institutional trading systems (like BlackRock's Aladdin). It:
1. Calculates technical indicators (RSI, MACD, Bollinger Bands, etc.)
2. Evaluates momentum, trend, and volatility
3. Combines signals into a composite score
4. Generates actionable recommendations

The approach is transparent and educational - every decision can be traced
to specific indicator conditions.
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class IndicatorPredictor:
    """Formula-based prediction using technical analysis"""
    
    def __init__(self):
        """Initialize the indicator-based predictor"""
        logger.info("✅ Indicator Predictor initialized")
    
    # ========================================
    # INDICATOR CALCULATIONS
    # ========================================
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """
        Calculate Relative Strength Index (RSI)
        
        RSI measures momentum on a 0-100 scale:
        - RSI > 70: Overbought (potential sell signal)
        - RSI < 30: Oversold (potential buy signal)
        - RSI 40-60: Neutral
        
        Formula:
            RSI = 100 - (100 / (1 + RS))
            where RS = Average Gain / Average Loss over period
        
        Args:
            prices: Price series
            period: Lookback period (default 14)
            
        Returns:
            float: RSI value (0-100)
        """
        delta = prices.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return float(rsi.iloc[-1]) if len(rsi) > 0 else 50.0
    
    def calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, float]:
        """
        Calculate MACD (Moving Average Convergence Divergence)
        
        MACD identifies trend changes and momentum:
        - MACD > Signal: Bullish (upward momentum)
        - MACD < Signal: Bearish (downward momentum)
        - MACD crossing above Signal: Buy signal
        - MACD crossing below Signal: Sell signal
        
        Formula:
            MACD Line = EMA(12) - EMA(26)
            Signal Line = EMA(9) of MACD Line
            Histogram = MACD Line - Signal Line
        
        Args:
            prices: Price series
            fast, slow, signal: EMA periods
            
        Returns:
            dict: MACD line, signal line, histogram
        """
        exp_fast = prices.ewm(span=fast, adjust=False).mean()
        exp_slow = prices.ewm(span=slow, adjust=False).mean()
        
        macd_line = exp_fast - exp_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        
        return {
            'macd': float(macd_line.iloc[-1]),
            'signal': float(signal_line.iloc[-1]),
            'histogram': float(histogram.iloc[-1])
        }
    
    def calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: float = 2.0) -> Dict[str, float]:
        """
        Calculate Bollinger Bands
        
        Bollinger Bands measure volatility and potential reversal points:
        - Price at upper band: Potentially overbought
        - Price at lower band: Potentially oversold
        - Band width: Indicates volatility (wide = high vol, narrow = low vol)
        
        Formula:
            Middle Band = SMA(20)
            Upper Band = Middle + (2 × StdDev)
            Lower Band = Middle - (2 × StdDev)
        
        Args:
            prices: Price series
            period: SMA period
            std_dev: Number of standard deviations
            
        Returns:
            dict: Upper, middle, lower bands and current position
        """
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        
        upper = sma + (std_dev * std)
        lower = sma - (std_dev * std)
        
        current_price = float(prices.iloc[-1])
        upper_band = float(upper.iloc[-1])
        middle_band = float(sma.iloc[-1])
        lower_band = float(lower.iloc[-1])
        
        # Calculate position within bands (0-1 scale)
        if upper_band > lower_band:
            position = (current_price - lower_band) / (upper_band - lower_band)
        else:
            position = 0.5
        
        return {
            'upper': upper_band,
            'middle': middle_band,
            'lower': lower_band,
            'position': position,  # 0 = at lower, 0.5 = at middle, 1 = at upper
            'width': upper_band - lower_band
        }
    
    def calculate_moving_averages(self, prices: pd.Series) -> Dict[str, float]:
        """
        Calculate key moving averages for trend identification
        
        Moving averages smooth price data to identify trends:
        - Price > MA: Uptrend
        - Price < MA: Downtrend
        - MA50 > MA200: "Golden Cross" (bullish)
        - MA50 < MA200: "Death Cross" (bearish)
        
        Args:
            prices: Price series
            
        Returns:
            dict: MA20, MA50, MA200 values
        """
        return {
            'ma20': float(prices.rolling(window=20).mean().iloc[-1]),
            'ma50': float(prices.rolling(window=50).mean().iloc[-1]),
            'ma200': float(prices.rolling(window=200).mean().iloc[-1]) if len(prices) >= 200 else None
        }
    
    def calculate_volume_profile(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Analyze volume patterns
        
        Volume confirms price moves:
        - High volume + price up: Strong buying (bullish)
        - High volume + price down: Strong selling (bearish)
        - Low volume moves: Weak conviction
        
        Args:
            df: DataFrame with 'close' and 'volume' columns
            
        Returns:
            dict: Volume metrics
        """
        if 'volume' not in df.columns:
            return {'delta': 0, 'trend': 'unknown'}
        
        # Simple volume delta (current vs average)
        current_vol = float(df['volume'].iloc[-1])
        avg_vol = float(df['volume'].rolling(window=20).mean().iloc[-1])
        
        # Volume trend
        vol_change = (current_vol - avg_vol) / avg_vol if avg_vol > 0 else 0
        
        return {
            'current': current_vol,
            'average': avg_vol,
            'delta_pct': vol_change * 100,
            'trend': 'increasing' if vol_change > 0.2 else ('decreasing' if vol_change < -0.2 else 'stable')
        }
    
    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """
        Calculate Average True Range (ATR)
        
        ATR measures volatility:
        - High ATR: High volatility (larger price swings)
        - Low ATR: Low volatility (smaller price swings)
        
        Used for:
        - Setting stop-loss distances
        - Position sizing
        - Risk management
        
        Args:
            df: DataFrame with OHLC data
            period: Lookback period
            
        Returns:
            float: ATR value
        """
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()
        
        return float(atr.iloc[-1]) if len(atr) > 0 else 0.0
    
    # ========================================
    # INDICATOR AGGREGATION
    # ========================================
    
    def compute_all_indicators(self, df: pd.DataFrame) -> Dict:
        """
        Calculate all technical indicators
        
        Args:
            df: OHLCV DataFrame
            
        Returns:
            dict: All indicator values
        """
        logger.info("📊 Computing all technical indicators...")
        
        prices = df['close']
        
        indicators = {
            'rsi': self.calculate_rsi(prices),
            'macd': self.calculate_macd(prices),
            'bb': self.calculate_bollinger_bands(prices),
            'ma': self.calculate_moving_averages(prices),
            'volume': self.calculate_volume_profile(df),
            'atr': self.calculate_atr(df),
            'current_price': float(prices.iloc[-1])
        }
        
        logger.info(f"   RSI: {indicators['rsi']:.1f}")
        logger.info(f"   MACD: {indicators['macd']['macd']:.2f} vs Signal: {indicators['macd']['signal']:.2f}")
        logger.info(f"   Price vs MA50: {indicators['current_price']:.2f} vs {indicators['ma']['ma50']:.2f}")
        
        return indicators
    
    # ========================================
    # SIGNAL SCORING & DECISION LOGIC
    # ========================================
    
    def score_momentum(self, indicators: Dict) -> Tuple[int, str]:
        """
        Score momentum indicators (RSI, MACD)
        
        Returns:
            tuple: (score, explanation)
                score: -2 to +2 (bearish to bullish)
        """
        score = 0
        reasons = []
        
        # RSI Analysis
        rsi = indicators['rsi']
        if rsi > 70:
            score -= 2
            reasons.append(f"RSI overbought ({rsi:.1f} > 70)")
        elif rsi > 60:
            score -= 1
            reasons.append(f"RSI elevated ({rsi:.1f})")
        elif rsi < 30:
            score += 2
            reasons.append(f"RSI oversold ({rsi:.1f} < 30)")
        elif rsi < 40:
            score += 1
            reasons.append(f"RSI low ({rsi:.1f})")
        else:
            reasons.append(f"RSI neutral ({rsi:.1f})")
        
        # MACD Analysis
        macd = indicators['macd']['macd']
        signal = indicators['macd']['signal']
        if macd > signal:
            score += 1
            reasons.append(f"MACD bullish ({macd:.2f} > {signal:.2f})")
        else:
            score -= 1
            reasons.append(f"MACD bearish ({macd:.2f} < {signal:.2f})")
        
        explanation = "; ".join(reasons)
        return score, explanation
    
    def score_trend(self, indicators: Dict) -> Tuple[int, str]:
        """
        Score trend indicators (Moving Averages)
        
        Returns:
            tuple: (score, explanation)
        """
        score = 0
        reasons = []
        
        price = indicators['current_price']
        ma50 = indicators['ma']['ma50']
        ma200 = indicators['ma']['ma200']
        
        # Price vs MA50
        if price > ma50:
            score += 1
            reasons.append(f"Price above MA50 (uptrend)")
        else:
            score -= 1
            reasons.append(f"Price below MA50 (downtrend)")
        
        # Golden/Death Cross (if MA200 available)
        if ma200:
            if ma50 > ma200:
                score += 1
                reasons.append("MA50 > MA200 (golden cross)")
            else:
                score -= 1
                reasons.append("MA50 < MA200 (death cross)")
        
        explanation = "; ".join(reasons)
        return score, explanation
    
    def score_volatility(self, indicators: Dict) -> Tuple[int, str]:
        """
        Score volatility conditions (Bollinger Bands, ATR)
        
        Returns:
            tuple: (score, explanation)
        """
        score = 0
        reasons = []
        
        # Bollinger Band position
        bb_position = indicators['bb']['position']
        if bb_position > 0.9:
            score -= 1
            reasons.append("At upper BB (overbought)")
        elif bb_position < 0.1:
            score += 1
            reasons.append("At lower BB (oversold)")
        else:
            reasons.append("Mid-BB range")
        
        # ATR (high volatility reduces confidence)
        atr = indicators['atr']
        price = indicators['current_price']
        atr_pct = (atr / price) * 100 if price > 0 else 0
        
        if atr_pct > 5:
            reasons.append(f"High volatility (ATR {atr_pct:.1f}%)")
        elif atr_pct < 2:
            reasons.append(f"Low volatility (ATR {atr_pct:.1f}%)")
        else:
            reasons.append(f"Normal volatility")
        
        explanation = "; ".join(reasons)
        return score, explanation
    
    def score_volume(self, indicators: Dict) -> Tuple[int, str]:
        """
        Score volume confirmation
        
        Returns:
            tuple: (score, explanation)
        """
        score = 0
        reasons = []
        
        vol = indicators['volume']
        if vol['trend'] == 'increasing':
            score += 1
            reasons.append(f"Volume increasing ({vol['delta_pct']:.1f}%)")
        elif vol['trend'] == 'decreasing':
            score -= 1
            reasons.append(f"Volume decreasing ({vol['delta_pct']:.1f}%)")
        else:
            reasons.append("Volume stable")
        
        explanation = "; ".join(reasons)
        return score, explanation
    
    def generate_signal(self, indicators: Dict) -> Dict:
        """
        Generate trading signal based on all indicators
        
        This is the main decision function that combines all scores
        into a final recommendation, similar to institutional
        decision-making systems (like BlackRock's Aladdin).
        
        Args:
            indicators: Dict of all technical indicators
            
        Returns:
            dict: Signal, confidence, target, summary
        """
        logger.info("\n🎯 GENERATING SIGNAL...")
        
        # Score each category
        momentum_score, momentum_reasons = self.score_momentum(indicators)
        trend_score, trend_reasons = self.score_trend(indicators)
        vol_score, vol_reasons = self.score_volatility(indicators)
        volume_score, volume_reasons = self.score_volume(indicators)
        
        # Compute total score
        total_score = momentum_score + trend_score + vol_score + volume_score
        max_score = 8  # Maximum possible score
        
        logger.info(f"   Momentum: {momentum_score:+d} | {momentum_reasons}")
        logger.info(f"   Trend: {trend_score:+d} | {trend_reasons}")
        logger.info(f"   Volatility: {vol_score:+d} | {vol_reasons}")
        logger.info(f"   Volume: {volume_score:+d} | {volume_reasons}")
        logger.info(f"   TOTAL SCORE: {total_score:+d} / {max_score}")
        
        # Determine signal
        if total_score >= 3:
            signal = "BUY"
            direction = "up"
        elif total_score <= -3:
            signal = "SELL"
            direction = "down"
        else:
            signal = "HOLD"
            direction = "neutral"
        
        # Calculate confidence (0-100%)
        confidence = min(abs(total_score) / max_score * 100, 95)
        
        # Estimate price target
        current_price = indicators['current_price']
        atr = indicators['atr']
        
        if signal == "BUY":
            # Target: Current + (1-2 × ATR)
            target_price = current_price + (1.5 * atr)
            pct_change = ((target_price - current_price) / current_price) * 100
        elif signal == "SELL":
            # Target: Current - (1-2 × ATR)
            target_price = current_price - (1.5 * atr)
            pct_change = ((target_price - current_price) / current_price) * 100
        else:
            target_price = current_price
            pct_change = 0
        
        # Build natural language summary
        summary = self.build_summary(
            signal=signal,
            confidence=confidence,
            current_price=current_price,
            target_price=target_price,
            pct_change=pct_change,
            indicators=indicators,
            reasons={
                'momentum': momentum_reasons,
                'trend': trend_reasons,
                'volatility': vol_reasons,
                'volume': volume_reasons
            }
        )
        
        result = {
            'signal': signal,
            'direction': direction,
            'confidence': round(confidence, 1),
            'current_price': round(current_price, 2),
            'target_price': round(target_price, 2),
            'pct_change': round(pct_change, 2),
            'summary': summary,
            'score_breakdown': {
                'momentum': momentum_score,
                'trend': trend_score,
                'volatility': vol_score,
                'volume': volume_score,
                'total': total_score
            },
            'indicators': indicators
        }
        
        logger.info(f"\n✅ SIGNAL: {signal} | Confidence: {confidence:.1f}% | Target: ${target_price:.2f} ({pct_change:+.1f}%)\n")
        
        return result
    
    def build_summary(self, signal: str, confidence: float, current_price: float, 
                     target_price: float, pct_change: float, indicators: Dict, reasons: Dict) -> str:
        """
        Build natural language recommendation summary
        
        This creates a user-friendly explanation of the prediction,
        similar to what an analyst might write.
        """
        # Start with market condition
        rsi = indicators['rsi']
        if rsi > 70:
            condition = f"Market is overbought (RSI {rsi:.1f} > 70)"
        elif rsi < 30:
            condition = f"Market is oversold (RSI {rsi:.1f} < 30)"
        else:
            condition = f"Market momentum is neutral (RSI {rsi:.1f})"
        
        # Add trend context
        trend_context = reasons['trend'].split(';')[0]  # First reason
        
        # Build recommendation
        if signal == "BUY":
            action = f"**BUY** signal detected"
            advice = f"Consider entering long position near ${current_price:.2f}"
            if pct_change > 0:
                advice += f" with target ${target_price:.2f} (+{pct_change:.1f}%)"
        elif signal == "SELL":
            action = f"**SELL** signal detected"
            advice = f"Consider exiting longs or entering short near ${current_price:.2f}"
            if pct_change < 0:
                advice += f" with target ${target_price:.2f} ({pct_change:.1f}%)"
        else:
            action = "**HOLD/WAIT** - No clear signal"
            advice = f"Current price ${current_price:.2f}. Wait for clearer setup"
        
        # Combine into summary
        summary = (
            f"{condition}. {trend_context}. "
            f"{action}. {advice}. "
            f"Confidence: {confidence:.0f}%."
        )
        
        return summary
    
    # ========================================
    # MAIN PREDICTION FUNCTION
    # ========================================
    
    def predict(self, ohlcv_data: pd.DataFrame) -> Dict:
        """
        Main prediction function
        
        Args:
            ohlcv_data: DataFrame with OHLCV columns
            
        Returns:
            dict: Complete prediction result
        """
        logger.info("\n" + "="*70)
        logger.info("INDICATOR-BASED PREDICTION")
        logger.info("="*70)
        
        # Compute all indicators
        indicators = self.compute_all_indicators(ohlcv_data)
        
        # Generate signal and recommendation
        result = self.generate_signal(indicators)
        
        # Add metadata
        result['mode'] = 'indicator'
        result['timestamp'] = pd.Timestamp.now().isoformat()
        
        logger.info("="*70 + "\n")
        
        return result


# ========================================
# MODULE EXPORTS
# ========================================

__all__ = ['IndicatorPredictor']

