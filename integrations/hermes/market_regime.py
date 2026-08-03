"""Market Regime Detection Module

Detects current market regime: uptrend, downtrend, range, chop, breakout.
Uses ADX, price action, Bollinger Bands for classification.
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional
import logging
from exchange_prices import get_ohlcv_data

logger = logging.getLogger(__name__)


class MarketRegime:
    """Market regime detection and analysis"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {
            'adx_threshold': 25,
            'range_threshold': 20,
            'bb_width_multiplier': 1.5,
            'lookback_candles': 14
        }
    
    def detect(self, symbol: str, timeframe: str = '1h') -> Dict:
        """Detect current market regime
        
        Args:
            symbol: Trading pair (e.g. 'BTCUSDT')
            timeframe: Candle timeframe
            
        Returns:
            Dict with regime, strength, and supporting metrics
        """
        try:
            # Get OHLCV data
            df = get_ohlcv_data(symbol, timeframe, limit=100)
            
            # Calculate indicators
            adx = self._calculate_adx(df)
            bb_width = self._calculate_bb_width(df)
            price_trend = self._calculate_trend(df)
            
            # Determine regime
            regime = self._classify_regime(adx, bb_width, price_trend)
            
            return {
                'regime': regime['type'],
                'strength': regime['strength'],
                'adx': adx,
                'bb_width': bb_width,
                'price_trend': price_trend,
                'confidence': regime['confidence']
            }
        except Exception as e:
            logger.error(f"Error detecting regime for {symbol}: {e}")
            return {'regime': 'unknown', 'strength': 0, 'confidence': 0}
    
    def _calculate_adx(self, df: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average Directional Index"""
        high = df['high']
        low = df['low']
        close = df['close']
        
        # +DM and -DM
        plus_dm = high.diff()
        minus_dm = -low.diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        
        # True Range
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Smoothed values
        atr = tr.rolling(period).mean()
        plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(period).mean() / atr)
        
        # ADX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(period).mean()
        
        return float(adx.iloc[-1]) if not adx.empty else 0
    
    def _calculate_bb_width(self, df: pd.DataFrame, period: int = 20, std: float = 2) -> float:
        """Calculate Bollinger Band width as percentage"""
        close = df['close']
        sma = close.rolling(period).mean()
        rolling_std = close.rolling(period).std()
        
        upper_band = sma + (rolling_std * std)
        lower_band = sma - (rolling_std * std)
        
        bb_width = ((upper_band - lower_band) / sma * 100).iloc[-1]
        return float(bb_width) if not np.isnan(bb_width) else 0
    
    def _calculate_trend(self, df: pd.DataFrame, period: int = 20) -> float:
        """Calculate price trend direction (-1 to 1)"""
        close = df['close']
        sma = close.rolling(period).mean()
        
        # Normalize trend
        current_price = close.iloc[-1]
        sma_value = sma.iloc[-1]
        
        if sma_value == 0:
            return 0
        
        trend = (current_price - sma_value) / sma_value
        return float(np.clip(trend * 100, -1, 1))
    
    def _classify_regime(self, adx: float, bb_width: float, trend: float) -> Dict:
        """Classify market regime based on indicators"""
        adx_thresh = self.config['adx_threshold']
        range_thresh = self.config['range_threshold']
        bb_mult = self.config['bb_width_multiplier']
        
        # Strong trend
        if adx > adx_thresh:
            if trend > 0.3:
                regime_type = 'uptrend'
                strength = min(adx / 50, 1.0)
            elif trend < -0.3:
                regime_type = 'downtrend'
                strength = min(adx / 50, 1.0)
            else:
                regime_type = 'chop'
                strength = 0.5
        # Range-bound
        elif adx < range_thresh and bb_width < bb_mult:
            regime_type = 'range'
            strength = 1 - (adx / range_thresh)
        # Breakout
        elif bb_width > bb_mult * 1.5:
            if trend > 0:
                regime_type = 'breakout_up'
            else:
                regime_type = 'breakout_down'
            strength = min(bb_width / (bb_mult * 2), 1.0)
        else:
            regime_type = 'neutral'
            strength = 0.3
        
        # Calculate confidence
        confidence = self._calculate_confidence(adx, bb_width, trend, regime_type)
        
        return {
            'type': regime_type,
            'strength': round(strength, 2),
            'confidence': round(confidence, 2)
        }
    
    def _calculate_confidence(self, adx: float, bb_width: float, trend: float, regime: str) -> float:
        """Calculate confidence score for regime classification"""
        # Base confidence on indicator alignment
        confidence_factors = []
        
        if regime in ['uptrend', 'downtrend']:
            confidence_factors.append(min(adx / 50, 1.0))
            confidence_factors.append(abs(trend))
        elif regime == 'range':
            confidence_factors.append(1 - min(adx / 25, 1.0))
            confidence_factors.append(1 - min(bb_width / 5, 1.0))
        elif regime in ['breakout_up', 'breakout_down']:
            confidence_factors.append(min(bb_width / 10, 1.0))
            confidence_factors.append(min(adx / 40, 1.0))
        
        return np.mean(confidence_factors) if confidence_factors else 0.5


# Convenience function
def detect_regime(symbol: str, timeframe: str = '1h', config: Optional[Dict] = None) -> Dict:
    """Quick regime detection
    
    Example:
        >>> regime = detect_regime('BTCUSDT', '1h')
        >>> print(regime['regime'])  # 'uptrend'
    """
    detector = MarketRegime(config)
    return detector.detect(symbol, timeframe)


if __name__ == '__main__':
    # Test
    logging.basicConfig(level=logging.INFO)
    result = detect_regime('BTCUSDT', '1h')
    print(f"Regime: {result['regime']}")
    print(f"Strength: {result['strength']}")
    print(f"Confidence: {result['confidence']}")
    print(f"ADX: {result['adx']:.2f}")
    print(f"BB Width: {result['bb_width']:.2f}%")
    print(f"Trend: {result['price_trend']:.3f}")
