import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config_loader import cfg
from deep_binance_analysis import get_macro_context, scan_market
from exchange_prices import get_price, get_order_book, estimate_slippage
from options_data import get_options_iv

logger = logging.getLogger(__name__)

SIGNALS_LOG = Path(__file__).parent / 'signals_log.jsonl'

DEFAULT_ACCOUNT_USDT = cfg.risk.default_account_usdt
DEFAULT_RISK_PCT = cfg.risk.default_risk_pct
DEFAULT_LEVERAGE = cfg.risk.default_leverage
MAX_PRIORITIES = 8
MAX_CANDIDATES = 15


class PositionSizer:
    def __init__(self, account_usdt: float = DEFAULT_ACCOUNT_USDT, risk_pct: float = DEFAULT_RISK_PCT, leverage: int = DEFAULT_LEVERAGE):
        self.account_usdt = account_usdt
        self.risk_pct = risk_pct
        self.leverage = leverage

    def size(self, entry: float, stop: float) -> dict[str, Any] | None:
        risk_per_contract = abs(entry - stop)
        risk_amount = self.account_usdt * self.risk_pct
        if risk_per_contract <= 0:
            return None

        qty = risk_amount / risk_per_contract
        max_notional = self.account_usdt * self.leverage
        notional = qty * entry
        capped = False
        if notional > max_notional:
            capped = True
            qty = max_notional / entry
            notional = qty * entry

        return {
            'qty': round(qty, 4),
            'risk_amount': round(risk_amount, 2),
            'position_notional': round(notional, 2),
            'max_notional': round(max_notional, 2),
            'risk_per_contract': round(risk_per_contract, 6),
            'formula': f"qty = {risk_amount:.0f} / |entry - stop|",
            'capped_by_leverage': capped,
        }


class BaseDirectionalAgent:
    name: str = 'base'
    direction: str | None = None

    def matches(self, row: dict[str, Any]) -> bool:
        raise NotImplementedError

    def build_signal(self, row: dict[str, Any], macro: dict[str, Any], sizer: PositionSizer) -> dict[str, Any] | None:
        raise NotImplementedError

    def evaluate(self, rows: list[dict[str, Any]], macro: dict[str, Any], account_usdt: float = DEFAULT_ACCOUNT_USDT) -> list[dict[str, Any]]:
        top_rows = rows[:MAX_CANDIDATES]
        filtered = [row for row in top_rows if self.matches(row)]
        signals: list[dict[str, Any]] = []
        sizer = PositionSizer(account_usdt=account_usdt)
        for row in filtered[:MAX_PRIORITIES]:
            signal = self.build_signal(row, macro, sizer)
            if signal:
                signals.append(signal)
        return signals

    def format_signal(self, signal: dict[str, Any] | None) -> str | None:
        if signal is None:
            return None
        leverage = signal.get('leverage', 1)
        rr1 = signal.get('rr1', 0) or 0
        rr2 = signal.get('rr2', 0) or 0
        rr3 = signal.get('rr3', 0) or 0
        alloc = signal.get('allocation_pcts', [])
        tp1_a = f" ({alloc[0]}%)" if len(alloc) > 0 else ""
        tp2_a = f" ({alloc[1]}%)" if len(alloc) > 1 else ""
        tp3_a = f" ({alloc[2]}%)" if len(alloc) > 2 else ""
        lines = [
            f"{signal['symbol']} | {signal['direction']} | score={signal['score']:.1f} | {signal.get('mode','')} | {leverage}x",
            f"Entry: {signal['entry_low']:.6f} - {signal['entry_high']:.6f}",
            f"Stop: {signal['stop']:.6f}",
            f"TP1: {signal['tp1']:.6f}{tp1_a} | TP2: {signal['tp2']:.6f}{tp2_a} | TP3: {signal['tp3']:.6f}{tp3_a}",
            f"R:R: {rr1:.2f} / {rr2:.2f} / {rr3:.2f}",
            f"Risk: {signal['risk_amount']:.0f} USDT | hold: {signal['holding']}",
            f"Cancel: {signal['cancel_condition']}",
            f"Reason: {signal['reason']}"
        ]
        return '\n'.join(lines)


class LongAgent(BaseDirectionalAgent):
    name = 'long'
    direction = 'LONG'

    def __init__(self, mode: str = "intraday") -> None:
        self.c = cfg.agents.long
        self.mc = getattr(cfg.trading_modes, mode, cfg.trading_modes.intraday)
        self.mode_name = mode

    def matches(self, row: dict[str, Any]) -> bool:
        bull_count = sum(1 for trend in [row['trend_4h'], row['trend_1h'], row['trend_15m']] if trend == 'bullish')
        return (
            bull_count >= self.c.min_bull_count
            and row['trend_4h'] == 'bullish'
            and row['oi_notional'] >= self.mc.min_oi_notional
            and row['vol_spike'] >= self.mc.min_vol_spike
            and row['spread_pct'] < self.mc.max_spread_pct
        )

    def build_signal(self, row: dict[str, Any], macro: dict[str, Any], sizer: PositionSizer) -> dict[str, Any] | None:
        mc = self.mc
        support = max(row['support_15m'], row['support_1h'])
        atr = row[mc.atr_tf]
        entry_low = support + atr * mc.entry_atr_low
        entry_high = support + atr * mc.entry_atr_high
        entry = min(max(row['price'], entry_low), entry_high)
        stop = support - atr * mc.stop_atr_mult
        tp1 = entry + max(atr * mc.tp1_atr_mult, (entry - stop) * mc.tp1_rr_min)
        tp2 = entry + max(atr * mc.tp2_atr_mult, (entry - stop) * mc.tp2_rr_min)
        tp3 = entry + max(atr * mc.tp3_atr_mult, (entry - stop) * (mc.tp2_rr_min + 0.5))
        rr1 = (tp1 - entry) / (entry - stop) if entry > stop else 0
        rr2 = (tp2 - entry) / (entry - stop) if entry > stop else 0
        rr3 = (tp3 - entry) / (entry - stop) if entry > stop else 0
        sizing = sizer.__class__(account_usdt=sizer.account_usdt, risk_pct=mc.risk_pct, leverage=mc.leverage).size(entry, stop)
        risk_note = 'normal risk' if sizing and sizing['risk_amount'] <= sizer.account_usdt * 0.02 else 'aggressive, consider lower risk' if sizing else 'invalid sizing'
        if rr1 < 1.5:
            risk_note = 'low R:R, wait for cleaner structure or smaller position'

        return {
            'symbol': row['symbol'],
            'category': row['category'],
            'direction': self.direction,
            'score': row['score'],
            'mode': f"futures_{self.mode_name}",
            'leverage': mc.leverage,
            'entry_low': entry_low,
            'entry_high': entry_high,
            'stop': stop,
            'tp1': tp1,
            'tp2': tp2,
            'tp3': tp3,
            'rr1': rr1,
            'rr2': rr2,
            'rr3': rr3,
            'allocation_pcts': mc.allocation_pcts,
            'qty': sizing['qty'] if sizing else 0,
            'notional': sizing['position_notional'] if sizing else 0,
            'risk_amount': sizing['risk_amount'] if sizing else 0,
            'size_formula': sizing['formula'] if sizing else '',
            'risk_note': risk_note,
            'holding': 'scalp' if self.mode_name == 'scalp' else 'intra-day/swing',
            'cancel_condition': 'close below 1h support or macro risk-off',
            'reason': 'trend alignment, liquidity, funding and capital flow',
        }


class ShortAgent(BaseDirectionalAgent):
    name = 'short'
    direction = 'SHORT'

    def __init__(self, mode: str = "intraday") -> None:
        self.c = cfg.agents.short
        self.mc = getattr(cfg.trading_modes, mode, cfg.trading_modes.intraday)
        self.mode_name = mode

    def matches(self, row: dict[str, Any]) -> bool:
        bear_count = sum(1 for trend in [row['trend_4h'], row['trend_1h'], row['trend_15m']] if trend == 'bearish')
        return (
            bear_count >= self.c.min_bear_count
            and row['trend_4h'] == 'bearish'
            and row['oi_notional'] >= self.mc.min_oi_notional
            and row['vol_spike'] >= self.mc.min_vol_spike
            and row['spread_pct'] < self.mc.max_spread_pct
        )

    def build_signal(self, row: dict[str, Any], macro: dict[str, Any], sizer: PositionSizer) -> dict[str, Any] | None:
        mc = self.mc
        resistance = min(row['resistance_15m'], row['resistance_1h'])
        atr = row[mc.atr_tf]
        entry_high = resistance - atr * mc.entry_atr_low
        entry_low = resistance - atr * mc.entry_atr_high
        entry = max(min(row['price'], entry_high), entry_low)
        stop = resistance + atr * mc.stop_atr_mult
        tp1 = entry - max(atr * mc.tp1_atr_mult, (stop - entry) * mc.tp1_rr_min)
        tp2 = entry - max(atr * mc.tp2_atr_mult, (stop - entry) * mc.tp2_rr_min)
        tp3 = entry - max(atr * mc.tp3_atr_mult, (stop - entry) * (mc.tp2_rr_min + 0.5))
        rr1 = (entry - tp1) / (stop - entry) if stop > entry else 0
        rr2 = (entry - tp2) / (stop - entry) if stop > entry else 0
        rr3 = (entry - tp3) / (stop - entry) if stop > entry else 0
        sizing = sizer.__class__(account_usdt=sizer.account_usdt, risk_pct=mc.risk_pct, leverage=mc.leverage).size(entry, stop)
        risk_note = 'normal risk' if sizing and sizing['risk_amount'] <= sizer.account_usdt * 0.02 else 'aggressive, consider lower risk' if sizing else 'invalid sizing'
        if rr1 < 1.5:
            risk_note = 'low R:R, wait for cleaner structure or smaller position'

        return {
            'symbol': row['symbol'],
            'category': row['category'],
            'direction': self.direction,
            'score': row['score'],
            'mode': f"futures_{self.mode_name}",
            'leverage': mc.leverage,
            'entry_low': entry_low,
            'entry_high': entry_high,
            'stop': stop,
            'tp1': tp1,
            'tp2': tp2,
            'tp3': tp3,
            'rr1': rr1,
            'rr2': rr2,
            'rr3': rr3,
            'allocation_pcts': mc.allocation_pcts,
            'qty': sizing['qty'] if sizing else 0,
            'notional': sizing['position_notional'] if sizing else 0,
            'risk_amount': sizing['risk_amount'] if sizing else 0,
            'size_formula': sizing['formula'] if sizing else '',
            'risk_note': risk_note,
            'holding': 'scalp' if self.mode_name == 'scalp' else 'intra-day/swing',
            'cancel_condition': 'close above 1h resistance or macro risk-on',
            'reason': 'trend alignment, liquidity, funding and capital flow',
        }


class SpotAgent(BaseDirectionalAgent):
    name = 'spot'
    direction = 'LONG_SPOT'

    def __init__(self) -> None:
        self.c = cfg.agents.spot

    def matches(self, row: dict[str, Any]) -> bool:
        return row['trend_4h'] == 'bullish' and row['quote_volume'] > self.c.min_quote_volume and row['spread_pct'] < self.c.max_spread_pct

    def build_signal(self, row: dict[str, Any], macro: dict[str, Any], sizer: PositionSizer) -> dict[str, Any] | None:
        c = self.c
        entry = row['price']
        atr15 = row['atr15']
        support_1h = row.get('support_1h', entry - atr15 * c.stop_atr_mult)
        stop = max(support_1h - atr15 * 0.2, entry - atr15 * c.stop_atr_mult)
        if stop >= entry:
            stop = entry - atr15 * c.stop_atr_mult
        tp1 = entry + atr15 * c.tp1_atr_mult
        tp2 = tp1 + atr15
        tp3 = tp2 + atr15
        rr1 = (tp1 - entry) / (entry - stop) if entry > stop else 0
        rr2 = (tp2 - entry) / (entry - stop) if entry > stop else 0
        rr3 = (tp3 - entry) / (entry - stop) if entry > stop else 0
        sizing = sizer.__class__(account_usdt=sizer.account_usdt, risk_pct=cfg.risk.spot_risk_pct, leverage=1).size(entry, stop)
        return {
            'symbol': row['symbol'],
            'category': row['category'],
            'direction': 'SPOT_LONG',
            'score': row['score'],
            'mode': 'spot',
            'leverage': 1,
            'entry_low': entry,
            'entry_high': entry,
            'stop': stop,
            'tp1': tp1,
            'tp2': tp2,
            'tp3': tp3,
            'rr1': rr1,
            'rr2': rr2,
            'rr3': rr3,
            'allocation_pcts': [50, 30, 20],
            'qty': sizing['qty'] if sizing else 0,
            'notional': sizing['position_notional'] if sizing else 0,
            'risk_amount': sizing['risk_amount'] if sizing else 0,
            'size_formula': sizing['formula'] if sizing else '',
            'risk_note': 'spot conservative',
            'holding': 'multi-day',
            'cancel_condition': 'price closes below 4h support',
            'reason': 'spot trend + liquidity',
        }


class ArbAgent(BaseDirectionalAgent):
    name = 'arb'
    direction = 'ARBITRAGE'

    def __init__(self) -> None:
        self.c = cfg.agents.arb
        self._cache: dict[str, dict[str, Any]] = {}

    def _fetch_arb_data(self, sym: str, quote_volume: float) -> dict[str, Any] | None:
        import time
        now = time.monotonic()
        cached = self._cache.get(sym)
        if cached and (now - cached['ts']) < self.c.cache_ttl_sec:
            return cached['data']

        try:
            p_bin = get_price('binance', sym)
            p_byb = get_price('bybit', sym)
            p_mex = get_price('mexc', sym)
            prices = [("binance", p_bin), ("bybit", p_byb), ("mexc", p_mex)]
            prices = [(ex, p) for ex, p in prices if p is not None]
            if len(prices) < 2:
                self._cache[sym] = {'data': None, 'ts': now}
                return None
            prices_sorted = sorted(prices, key=lambda x: x[1])
            low_name, low_p = prices_sorted[0]
            high_name, high_p = prices_sorted[-1]
            spread = (high_p - low_p) / low_p if low_p else 0.0
            desired_notional = min(10_000, max(2_000, int(quote_volume * 0.001)))
            base_qty = desired_notional / low_p if low_p else 0
            book_buy = get_order_book(low_name, sym, limit=50)
            book_sell = get_order_book(high_name, sym, limit=50)
            slippage_buy = estimate_slippage(book_buy.get('asks', []), base_qty, reference_price=low_p) if book_buy else None
            slippage_sell = estimate_slippage(book_sell.get('bids', []), base_qty, reference_price=high_p) if book_sell else None
            fees_total = self.c.taker_fee_per_side * 2
            if slippage_buy is None or slippage_sell is None:
                effective_profit = None
            else:
                effective_profit = spread - fees_total - abs(slippage_buy) - abs(slippage_sell)
            data = {
                'prices': prices_sorted,
                'low_name': low_name, 'low_p': low_p,
                'high_name': high_name, 'high_p': high_p,
                'spread': spread,
                'slippage_buy': slippage_buy,
                'slippage_sell': slippage_sell,
                'fees_total': fees_total,
                'effective_profit': effective_profit,
                'desired_notional': desired_notional,
                'book_buy': book_buy,
                'book_sell': book_sell,
            }
            self._cache[sym] = {'data': data, 'ts': now}
            return data
        except Exception as exc:
            logger.debug("arb fetch failed for %s: %s", sym, exc)
            self._cache[sym] = {'data': None, 'ts': now}
            return None

    def matches(self, row: dict[str, Any]) -> bool:
        sym = row['symbol']
        data = self._fetch_arb_data(sym, row.get('quote_volume', 0))
        if not data:
            return False
        ep = data.get('effective_profit')
        if ep is None:
            return False
        return ep >= self.c.min_effective_profit and row.get('quote_volume', 0) > self.c.min_quote_volume

    def build_signal(self, row: dict[str, Any], macro: dict[str, Any], sizer: PositionSizer) -> dict[str, Any] | None:
        sym = row['symbol']
        data = self._fetch_arb_data(sym, row.get('quote_volume', 0))
        if not data:
            return None
        buy_ex = data['low_name']
        buy_p = data['low_p']
        sell_ex = data['high_name']
        sell_p = data['high_p']
        spread = data['spread']
        entry = buy_p
        stop = entry * 0.995
        est_effective = data['effective_profit']

        sizing = sizer.__class__(account_usdt=sizer.account_usdt, risk_pct=cfg.risk.arb_risk_pct, leverage=1).size(entry, stop)

        return {
            'symbol': sym,
            'category': row.get('category', 'alt'),
            'direction': 'ARB',
            'score': row['score'],
            'mode': 'arb',
            'leverage': 1,
            'rr1': 0,
            'rr2': 0,
            'buy_exchange': buy_ex,
            'sell_exchange': sell_ex,
            'buy_price': buy_p,
            'sell_price': sell_p,
            'spread': spread,
            'est_slippage_buy': data.get('slippage_buy'),
            'est_slippage_sell': data.get('slippage_sell'),
            'est_fees': data.get('fees_total'),
            'est_effective_profit': est_effective,
            'entry_low': entry,
            'entry_high': entry,
            'stop': stop,
            'tp1': sell_p,
            'tp2': sell_p * 1.001,
            'qty': sizing['qty'] if sizing else 0,
            'notional': sizing['position_notional'] if sizing else 0,
            'risk_amount': sizing['risk_amount'] if sizing else 0,
            'size_formula': sizing['formula'] if sizing else '',
            'risk_note': 'arb small allocation; account for fees and slippage',
            'holding': 'minutes',
            'cancel_condition': 'exchange liquidity changes or price convergence',
            'reason': f'arbitrage {buy_ex}->{sell_ex} spread {spread:.3%}',
        }


class OptionsAgent(BaseDirectionalAgent):
    name = 'options'
    direction = 'OPTIONS'

    def __init__(self) -> None:
        self.c = cfg.agents.options

    def matches(self, row: dict[str, Any]) -> bool:
        if row['symbol'] not in self.c.underlyings:
            return False
        return abs(row.get('funding', 0.0)) >= self.c.funding_extreme or abs(row.get('pct4h', 0)) >= self.c.move_extreme_pct

    def build_signal(self, row: dict[str, Any], macro: dict[str, Any], sizer: PositionSizer) -> dict[str, Any] | None:
        iv = get_options_iv(row['symbol'])
        note = 'options alert: extreme funding or move'
        if iv:
            note = f'options alert: ATM IV ~ {iv:.2f}'

        return {
            'symbol': row['symbol'],
            'category': row.get('category', 'alt'),
            'direction': 'OPTIONS_ALERT',
            'score': row['score'],
            'mode': 'options',
            'entry_low': row['price'],
            'entry_high': row['price'],
            'stop': row['price'],
            'tp1': row['price'],
            'tp2': row['price'],
            'qty': 0,
            'notional': 0,
            'risk_amount': 0,
            'size_formula': '',
            'risk_note': 'options: use IV and chain to size',
            'holding': 'short-term',
            'cancel_condition': 'no options data or illiquid chain',
            'reason': note,
            'atm_iv': iv,
        }


class MoonshotAgent(BaseDirectionalAgent):
    name = 'moonshot'
    direction = 'MOONSHOT'

    def __init__(self) -> None:
        self.c = cfg.agents.moonshot

    def matches(self, row: dict[str, Any]) -> bool:
        low_notional = row['oi_notional'] < 10_000_000
        low_price = row['price'] < self.c.max_price
        huge_spike = row['vol_spike'] >= self.c.min_vol_spike or abs(row['pct15']) >= 20 or abs(row.get('pct5m', 0)) >= 10
        meme_flag = row.get('category') == 'meme'
        return (huge_spike and (low_notional or low_price or meme_flag))

    def build_signal(self, row: dict[str, Any], macro: dict[str, Any], sizer: PositionSizer) -> dict[str, Any] | None:
        c = self.c
        entry = row['price']
        atr = row.get('atr5', row.get('atr15', 0.0))
        stop = max(0.0, entry - max(atr * 0.8, entry * 0.05))
        tp1 = entry * c.tp1_mult
        tp2 = entry * c.tp2_mult
        sizing = sizer.__class__(account_usdt=sizer.account_usdt, risk_pct=cfg.risk.moonshot_risk_pct, leverage=1).size(entry, stop)

        return {
            'symbol': row['symbol'],
            'category': row['category'],
            'direction': self.direction,
            'score': row['score'],
            'mode': 'futures/spot-hybrid',
            'leverage': 1,
            'entry_low': entry,
            'entry_high': entry,
            'stop': stop,
            'tp1': tp1,
            'tp2': tp2,
            'rr1': (tp1 - entry) / (entry - stop) if entry > stop and stop > 0 else 0,
            'rr2': (tp2 - entry) / (entry - stop) if entry > stop and stop > 0 else 0,
            'qty': sizing['qty'] if sizing else 0,
            'notional': sizing['position_notional'] if sizing else 0,
            'risk_amount': sizing['risk_amount'] if sizing else 0,
            'size_formula': sizing['formula'] if sizing else '',
            'risk_note': 'highly speculative; tiny allocation only',
            'holding': 'swing / lottery',
            'cancel_condition': 'sudden reversal / news negative',
            'reason': 'low liquidity + extreme spike / meme pattern',
        }


def append_signals_log(signals: list[dict[str, Any]], regime: str) -> None:
    ts = datetime.now(timezone.utc).isoformat()
    try:
        with open(SIGNALS_LOG, 'a', encoding='utf-8') as f:
            for sig in signals:
                record = {
                    'ts': ts,
                    'symbol': sig.get('symbol'),
                    'direction': sig.get('direction'),
                    'entry': sig.get('entry_low'),
                    'stop': sig.get('stop'),
                    'tp1': sig.get('tp1'),
                    'tp2': sig.get('tp2'),
                    'score': sig.get('score'),
                    'regime': regime,
                    'mode': sig.get('mode'),
                    'rr1': sig.get('rr1'),
                    'outcome': None,
                }
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
    except Exception as e:
        logger.warning("signals_log write error: %s", e)


def print_section(title: str, lines: list[Any]) -> None:
    print('=' * 72)
    print(title)
    print('=' * 72)
    for line in lines:
        if line is None:
            continue
        text = line if isinstance(line, str) else str(line)
        try:
            print(text)
        except UnicodeEncodeError:
            print(text.encode('ascii', 'replace').decode('ascii'))
    print()


def run_agents(account_usdt: float = DEFAULT_ACCOUNT_USDT) -> None:
    rows = scan_market()
    macro = get_macro_context(rows) if rows else {'summary': 'no data', 'events_text': ''}
    long_agent = LongAgent()
    short_agent = ShortAgent()
    spot_agent = SpotAgent()
    arb_agent = ArbAgent()

    long_signals = long_agent.evaluate(rows, macro, account_usdt=account_usdt)
    short_signals = short_agent.evaluate(rows, macro, account_usdt=account_usdt)
    spot_signals = spot_agent.evaluate(rows, macro, account_usdt=account_usdt)
    arb_signals = arb_agent.evaluate(rows, macro, account_usdt=account_usdt)

    print('TIME', datetime.now(timezone.utc).isoformat())
    print('SOURCE: directional_binance_agents')
    print()
    print_section('MACRO CONTEXT', [macro.get('summary', ''), f"Events: {macro.get('events_text', '')}"])

    if not rows:
        print('No market candidates available.')
        return

    print_section('PRIORITY UNIVERSE', [f"Top {min(len(rows), MAX_CANDIDATES)} candidates by score: {', '.join(r['symbol'] for r in rows[:MAX_CANDIDATES])}"])
    print_section('LONG SIGNALS', [long_agent.format_signal(s) for s in long_signals] if long_signals else ['No long signals at this time.'])
    print_section('SHORT SIGNALS', [short_agent.format_signal(s) for s in short_signals] if short_signals else ['No short signals at this time.'])
    print_section('SPOT SIGNALS', [spot_agent.format_signal(s) for s in spot_signals] if spot_signals else ['No spot signals at this time.'])
    print_section('ARB SIGNALS', [arb_agent.format_signal(s) for s in arb_signals] if arb_signals else ['No arb signals at this time.'])

    # persist all actionable signals for post-factum evaluation
    regime = macro.get('regime', 'unknown')
    all_actionable = long_signals + short_signals
    if all_actionable:
        append_signals_log(all_actionable, regime)
        print(f'[signals_log] +{len(all_actionable)} record(s) appended')


if __name__ == '__main__':
    run_agents()
