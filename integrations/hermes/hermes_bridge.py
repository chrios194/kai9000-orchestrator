#!/usr/bin/env python3
"""
Hermes Bridge — интеграция Hermes Foundation торговых агентов в KAI-9000.

Связывает:
  - Hermes 6 агентов (Long/Short/Spot/Arb/Moonshot/Options) → @CryptoStrategist субагент
  - market_regime.py → crypto-portfolio-monitor workflow
  - bot.py Telegram → KAI-9000 notifications
  - claude_client.py → KAI-9000 model layer

Usage:
  from hermes_bridge import HermesBridge
  bridge = HermesBridge()
  signals = bridge.get_signals(mode='intraday')
  regime = bridge.get_market_regime('BTCUSDT')
"""

import sys
import os
import json
import logging
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Путь к Hermes Foundation
HERMES_DIR = Path(__file__).resolve().parent
if str(HERMES_DIR) not in sys.path:
    sys.path.insert(0, str(HERMES_DIR))

try:
    from config_loader import cfg
    from deep_binance_analysis import scan_market, get_macro_context
    from directional_binance_agents import (
        LongAgent, ShortAgent, SpotAgent, ArbAgent,
        MoonshotAgent, DEFAULT_ACCOUNT_USDT,
    )
    from market_regime import MarketRegime
    from exchange_prices import get_price, get_order_book
    HERMES_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Hermes modules not available: {e}")
    HERMES_AVAILABLE = False


class HermesBridge:
    """Мост между Hermes Foundation и KAI-9000 оркестратором."""

    AGENTS = {
        'long': 'LongAgent',
        'short': 'ShortAgent',
        'spot': 'SpotAgent',
        'arb': 'ArbAgent',
        'moonshot': 'MoonshotAgent',
        'options': 'OptionsAgent',
    }

    def __init__(self, account_usdt: float = 10000):
        self.account_usdt = account_usdt
        if HERMES_AVAILABLE:
            self.regime_detector = MarketRegime(cfg)
            self.agents = {
                'long': LongAgent(),
                'short': ShortAgent(),
                'spot': SpotAgent(),
                'arb': ArbAgent(),
                'moonshot': MoonshotAgent(),
            }
        else:
            self.regime_detector = None
            self.agents = {}

    def get_signals(self, mode: str = 'intraday') -> list[dict]:
        """
        Получить торговые сигналы от всех агентов Hermes.
        
        Args:
            mode: 'scalp' | 'intraday' | 'swing'
        
        Returns:
            List of Sovereign Signal formatted dicts
        """
        if not HERMES_AVAILABLE:
            logger.error("Hermes modules not available")
            return []

        try:
            rows = scan_market()
            macro = get_macro_context()
            signals = []

            for agent_name, agent in self.agents.items():
                agent_signals = agent.evaluate(rows, macro, self.account_usdt)
                for sig in agent_signals:
                    # Конвертируем в Sovereign Signal format
                    sovereign = self._to_sovereign_signal(sig, agent_name, mode)
                    if sovereign:
                        signals.append(sovereign)

            # Сортируем по score
            signals.sort(key=lambda s: s.get('_hermes_score', 0), reverse=True)
            return signals[:10]  # Top 10

        except Exception as e:
            logger.error(f"Error getting signals: {e}")
            return []

    def get_market_regime(self, symbol: str = 'BTCUSDT') -> dict:
        """
        Получить рыночный режим через market_regime.py.
        Возвращает CRYPTO ORACLE enhanced формат.
        """
        if not HERMES_AVAILABLE or not self.regime_detector:
            return {'regime': 'unknown', 'confidence': 0}

        try:
            base = self.regime_detector.detect(symbol, '1h')
            
            # Enhance to 6-layer format
            enhanced = {
                'regime': base.get('regime', 'unknown'),
                'confidence': base.get('confidence', 0),
                'strength': base.get('strength', 0),
                'adx': base.get('adx', 0),
                'bb_width': base.get('bb_width', 0),
                'price_trend': base.get('price_trend', 0),
                # CRYPTO ORACLE 6-layer mapping
                'layers': {
                    'technical': {
                        'regime': base.get('regime'),
                        'adx': base.get('adx'),
                        'trend': base.get('price_trend'),
                    },
                    'onchain': None,  # Требует Glassnode/Nansen API
                    'derivatives': None,  # Требует Coinglass/Hyblock
                    'sentiment': None,  # Требует CryptoPanic/Twitter
                    'macro': None,  # Требует DXY/ETF flows
                    'fundamentals': None,  # Требует Token Terminal
                },
                'sovereign_verdict': self._regime_to_verdict(base),
            }
            return enhanced
        except Exception as e:
            logger.error(f"Error detecting regime: {e}")
            return {'regime': 'unknown', 'confidence': 0}

    def check_liquidation_risk(self, positions: list[dict]) -> list[dict]:
        """
        Проверка риска ликвидации для открытых позиций.
        CRITICAL ALERT если margin < 15%.
        """
        alerts = []
        for pos in positions:
            symbol = pos.get('symbol', '')
            entry = pos.get('entry', 0)
            leverage = pos.get('leverage', 1)
            current_price = get_price(cfg.exchange.name, symbol)

            if not current_price or not entry:
                continue

            # Расчёт PnL%
            pnl_pct = ((current_price - entry) / entry) * 100
            if pos.get('direction') == 'short':
                pnl_pct = -pnl_pct

            # Расчёт margin health
            liquidation_price = entry * (1 - 1/leverage)
            if pos.get('direction') == 'short':
                liquidation_price = entry * (1 + 1/leverage)

            distance_to_liq = abs(current_price - liquidation_price) / current_price * 100
            margin_health = distance_to_liq * leverage

            alert = {
                'symbol': symbol,
                'direction': pos.get('direction'),
                'entry': entry,
                'current_price': current_price,
                'pnl_pct': round(pnl_pct, 2),
                'leverage': leverage,
                'liquidation_price': round(liquidation_price, 6),
                'margin_health_pct': round(margin_health, 1),
                'severity': 'ok',
            }

            if margin_health < 15:
                alert['severity'] = 'CRITICAL'
                alert['message'] = f"🚨 LIQUIDATION RISK: {symbol} margin health {margin_health:.1f}%"
            elif margin_health < 25:
                alert['severity'] = 'warning'
                alert['message'] = f"⚠️ {symbol} margin health low: {margin_health:.1f}%"

            alerts.append(alert)

        return alerts

    def _to_sovereign_signal(self, hermes_sig: dict, agent_name: str, mode: str) -> Optional[dict]:
        """Конвертация Hermes signal → CRYPTO ORACLE Sovereign Signal format."""
        try:
            direction = hermes_sig.get('direction', agent_name)
            verdict_map = {
                'long': 'LONG',
                'short': 'SHORT',
                'spot': 'LONG',
            }
            verdict = verdict_map.get(direction, 'NEUTRAL')

            # Confidence на основе score
            score = hermes_sig.get('score', 0)
            if score > 100:
                confidence = 'C:95+'
            elif score > 70:
                confidence = 'C:80'
            elif score > 50:
                confidence = 'C:60'
            else:
                confidence = 'C:40'

            leverage = hermes_sig.get('leverage', 
                                     cfg.modes.get(mode, {}).get('leverage', 5))

            return {
                # Sovereign Signal format
                'VERDICT': verdict,
                'CONFIDENCE': confidence,
                'REGIME': self.get_market_regime(hermes_sig.get('symbol', 'BTCUSDT')).get('regime', 'unknown'),
                'SYMBOL': hermes_sig.get('symbol'),
                'ENTRY_ZONE': [hermes_sig.get('entry_low'), hermes_sig.get('entry_high')],
                'STOP_LOSS': hermes_sig.get('stop'),
                'TP1': hermes_sig.get('tp1'),
                'TP2': hermes_sig.get('tp2'),
                'TP3': hermes_sig.get('tp3'),
                'R:R': [hermes_sig.get('rr1', 0), hermes_sig.get('rr2', 0), hermes_sig.get('rr3', 0)],
                'LEVERAGE': f"{leverage}x",
                'POSITION_SIZE': hermes_sig.get('risk_amount'),
                'AGENT': agent_name,
                'MODE': mode,
                'REASON': hermes_sig.get('reason'),
                'CANCEL': hermes_sig.get('cancel_condition'),
                # Internal
                '_hermes_score': score,
                '_raw': hermes_sig,
            }
        except Exception as e:
            logger.error(f"Error converting signal: {e}")
            return None

    def _regime_to_verdict(self, regime_data: dict) -> str:
        """Маппинг regime → Sovereign Verdict."""
        r = regime_data.get('regime', 'unknown').lower()
        if 'bull' in r or 'trending_up' in r:
            return 'LONG'
        elif 'bear' in r or 'trending_down' in r:
            return 'SHORT'
        elif 'rang' in r:
            return 'NEUTRAL'
        elif 'high_vol' in r:
            return 'WAIT'
        else:
            return 'NO TRADE'

    def format_kai9000_briefing(self) -> str:
        """
        Форматирование краткого брифинга для KAI-9000 morning workflow.
        Возвращает Markdown-строку для Obsidian vault.
        """
        regime = self.get_market_regime('BTCUSDT')
        signals = self.get_signals('intraday')
        
        lines = [
            f"# KAI-9000 Crypto Briefing — {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"",
            f"## Market Regime",
            f"- **Regime**: {regime.get('regime', 'unknown')}",
            f"- **Confidence**: {regime.get('confidence', 0)}",
            f"- **ADX**: {regime.get('adx', 0)}",
            f"- **Sovereign Verdict**: {regime.get('sovereign_verdict', 'NO TRADE')}",
            f"",
            f"## Top Signals ({len(signals)})",
        ]
        
        for i, sig in enumerate(signals[:5], 1):
            lines.extend([
                f"",
                f"### {i}. {sig.get('SYMBOL', 'N/A')} — {sig.get('VERDICT')} [{sig.get('CONFIDENCE')}]",
                f"- **Agent**: {sig.get('AGENT')} | **Mode**: {sig.get('MODE')}",
                f"- **Entry**: {sig.get('ENTRY_ZONE')}",
                f"- **SL**: {sig.get('STOP_LOSS')} | **TP1**: {sig.get('TP1')} | **TP2**: {sig.get('TP2')} | **TP3**: {sig.get('TP3')}",
                f"- **R:R**: {sig.get('R:R')} | **Leverage**: {sig.get('LEVERAGE')}",
                f"- **Reason**: {sig.get('REASON')}",
            ])
        
        # Liquidation checks
        lines.extend([
            f"",
            f"## Critical Monitoring",
            f"- aUSDT: откат >0.5% от паритета → CRITICAL ALERT",
            f"- XAUt: отклонение >2% от цены золота → CRITICAL ALERT", 
            f"- XLM_PERP: маржа <15% → LIQUIDATION ALERT",
        ])
        
        return '\n'.join(lines)


if __name__ == "__main__":
    bridge = HermesBridge()
    print(bridge.format_kai9000_briefing())
