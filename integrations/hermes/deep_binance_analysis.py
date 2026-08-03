"""Deep market analysis using ccxt with Bybit Linear Perpetuals.

Scans the Bybit USDT perpetual market for high-scoring trading candidates
based on volume spikes, open interest, funding rates, order-book imbalance,
and multi-timeframe trend alignment.
"""

import logging
import re
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any

from config_loader import cfg
from exchange_prices import get_exchange
from news_feed import top_events_summary

logger = logging.getLogger(__name__)

SYMBOL_RE = re.compile(r'^[A-Z0-9]{2,15}USDT$')

MAJOR_SYMBOLS = {
    'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT', 'SOLUSDT',
    'ADAUSDT', 'DOGEUSDT', 'MATICUSDT', 'DOTUSDT', 'UNIUSDT',
}
MEME_PREFIXES = ('DOGE', 'SHIB', 'PEPE', 'ARB', 'MANA', 'SAND', 'CHZ', 'FTM', 'HNT')

_SCAN_CACHE: dict[str, Any] = {'ts': 0.0, 'rows': [], 'macro': {}}
_SCAN_CACHE_TTL = 300


def get_cached_scan(max_age: float = _SCAN_CACHE_TTL) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Return cached scan results or run a fresh scan if stale."""
    now = time.time()
    if now - _SCAN_CACHE['ts'] < max_age and _SCAN_CACHE['rows']:
        return _SCAN_CACHE['rows'], _SCAN_CACHE['macro']
    rows = scan_market()
    macro = get_macro_context(rows)
    _SCAN_CACHE['ts'] = now
    _SCAN_CACHE['rows'] = rows
    _SCAN_CACHE['macro'] = macro
    return rows, macro


def _get_exchange():
    """Get or create the Bybit ccxt exchange instance."""
    return get_exchange('bybit')


def _to_ccxt_symbol(symbol: str) -> str:
    """Convert flat symbol like 'BTCUSDT' to ccxt linear perp format 'BTC/USDT:USDT'."""
    # Strip the trailing 'USDT' to get the base
    base = symbol[:-4]
    return f'{base}/USDT:USDT'


def _from_ccxt_symbol(ccxt_symbol: str) -> str:
    """Convert ccxt symbol 'BTC/USDT:USDT' back to flat format 'BTCUSDT'."""
    # Extract base from 'BTC/USDT:USDT'
    base = ccxt_symbol.split('/')[0]
    return f'{base}USDT'


def categorize_symbol(symbol: str) -> str:
    """Categorize a symbol as major, meme, or alt."""
    if symbol in MAJOR_SYMBOLS:
        return 'major'
    if any(symbol.startswith(prefix) for prefix in MEME_PREFIXES):
        return 'meme'
    return 'alt'


def market_regime(rows: list[dict[str, Any]]) -> str:
    """Determine the overall market regime from the top rows."""
    if not rows:
        return 'unknown'

    sample = rows[:20]
    bull_count = sum(1 for r in sample if r['trend_4h'] == 'bullish')
    bear_count = sum(1 for r in sample if r['trend_4h'] == 'bearish')
    flat_count = sum(1 for r in sample if abs(r['pct4h']) < 0.35)
    avg_vol = statistics.mean(abs(r['pct4h']) for r in sample)

    if bull_count >= 14 and avg_vol > 0.5:
        return 'trend / risk-on'
    if bear_count >= 14 and avg_vol > 0.5:
        return 'trend / risk-off'
    if flat_count >= 12 and avg_vol < 0.3:
        return 'flat / low-volatility'
    if bull_count >= 6 and bear_count >= 6:
        return 'chaos / rotation'
    return 'mixed / rotation'


def format_pct(value: float) -> str:
    """Format a percentage value with sign."""
    return f"{value:+.2f}%"


def get_macro_context(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Build macro context dict from scan rows including BTC/ETH dominance and events."""
    btc = next((r for r in rows if r['symbol'] == 'BTCUSDT'), None)
    eth = next((r for r in rows if r['symbol'] == 'ETHUSDT'), None)
    total_quote = sum(r['quote_volume'] for r in rows) or 1
    btc_dom = btc['quote_volume'] / total_quote if btc else 0.0
    eth_dom = eth['quote_volume'] / total_quote if eth else 0.0
    regime = market_regime(rows)
    events: list[str] = []

    if btc:
        if abs(btc['funding']) >= 0.02:
            events.append('BTC funding pressure')
        if btc['oi_notional'] > 15e9:
            events.append('BTC OI elevated')
    if eth:
        if abs(eth['funding']) >= 0.02:
            events.append('ETH funding pressure')
        if eth['oi_notional'] > 9e9:
            events.append('ETH OI elevated')

    if not events:
        events.append('No acute funding/OI events')

    try:
        news = top_events_summary(limit=3)
        for n in news:
            events.append(f"NEWS: {n.get('kw','')} - {n.get('title','')}")
    except Exception as exc:
        logger.debug("news feed failed: %s", exc)

    return {
        'btc': btc,
        'eth': eth,
        'btc_dominance': btc_dom,
        'eth_dominance': eth_dom,
        'regime': regime,
        'events': events,
        'summary': (
            f"Macro regime: {regime} | "
            f"BTC 4h={btc['trend_4h'] if btc else 'n/a'} {format_pct(btc['pct4h']) if btc else 'n/a'} "
            f"({btc_dom*100:.1f}% vol) | "
            f"ETH 4h={eth['trend_4h'] if eth else 'n/a'} {format_pct(eth['pct4h']) if eth else 'n/a'} "
            f"({eth_dom*100:.1f}% vol)"
        ),
        'events_text': '; '.join(events),
    }


def atr(candles: list[list]) -> float:
    """Average True Range from ccxt OHLCV candles [[ts, o, h, l, c, vol], ...]."""
    return statistics.mean(
        [
            max(
                float(h) - float(l),
                abs(float(h) - float(c)),
                abs(float(l) - float(c)),
            )
            for _, o, h, l, c, *_ in candles
        ]
    )


def trend_direction(candles: list[list]) -> str:
    """Determine trend direction from first open to last close."""
    first_open = float(candles[0][1])
    last_close = float(candles[-1][4])
    return 'bullish' if last_close > first_open else 'bearish'


def candle_fresh(candles: list[list], interval: str) -> bool:
    """Check if the last candle is recent enough for the given interval."""
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    last_open = int(candles[-1][0])
    interval_ms = {
        '1m': 1 * 60 * 1000,
        '5m': 5 * 60 * 1000,
        '15m': 15 * 60 * 1000,
        '1h': 60 * 60 * 1000,
        '4h': 4 * 60 * 60 * 1000,
    }.get(interval, 15 * 60 * 1000)
    return abs(now_ms - last_open) <= interval_ms * 2


def build_candidate_row(t: dict[str, Any]) -> dict[str, Any] | None:
    """Build a full candidate row for a single ticker entry.

    Args:
        t: dict with keys 'symbol' (flat format like 'BTCUSDT'),
           'lastPrice' (float), 'quoteVolume' (float).

    Returns:
        Scored candidate dict or None if filtered out.
    """
    sym = t['symbol']
    price = float(t['lastPrice'])
    if price < cfg.scanner.min_price_usdt:
        return None

    exchange = _get_exchange()
    ccxt_sym = _to_ccxt_symbol(sym)

    # Fetch multi-timeframe OHLCV candles
    k5 = exchange.fetch_ohlcv(ccxt_sym, '5m', limit=30)
    k15 = exchange.fetch_ohlcv(ccxt_sym, '15m', limit=30)
    k60 = exchange.fetch_ohlcv(ccxt_sym, '1h', limit=30)
    k240 = exchange.fetch_ohlcv(ccxt_sym, '4h', limit=30)

    # Fetch funding rate
    funding_info = exchange.fetch_funding_rate(ccxt_sym)
    funding_rate = float(funding_info.get('fundingRate', 0.0) or 0.0)
    funding_ts = funding_info.get('fundingTimestamp') or funding_info.get('timestamp')

    # Fetch order book
    depth = exchange.fetch_order_book(ccxt_sym, limit=20)

    # Extract close and volume arrays
    close5 = [float(c[4]) for c in k5]
    close15 = [float(c[4]) for c in k15]
    close60 = [float(c[4]) for c in k60]
    close240 = [float(c[4]) for c in k240]
    vol15 = [float(c[5]) for c in k15]

    # Open interest
    oi = 0.0
    try:
        oi_info = exchange.fetch_open_interest(ccxt_sym)
        oi = float(oi_info.get('openInterestAmount', 0) or 0)
    except Exception as exc:
        logger.debug("OI fetch failed for %s: %s", sym, exc)

    # Volume spike calculation
    # Use second-to-last candle (last completed) vs average of prior candles
    # The very last candle may still be forming and have low volume
    if len(vol15) >= 3:
        last_complete_vol = vol15[-2]
        avg15_prior = statistics.mean(vol15[:-2])
        vol_spike = last_complete_vol / avg15_prior if avg15_prior else 1
    elif len(vol15) == 2:
        vol_spike = vol15[-2] / vol15[-1] if vol15[-1] else 1
    else:
        vol_spike = 1.0

    # Order book metrics
    best_bid = float(depth['bids'][0][0]) if depth['bids'] else price
    best_ask = float(depth['asks'][0][0]) if depth['asks'] else price
    bid_qty = sum(float(b[1]) for b in depth['bids'][:10])
    ask_qty = sum(float(a[1]) for a in depth['asks'][:10])
    ask_bid_imbalance = (ask_qty / bid_qty) if bid_qty else 1

    # Support/resistance levels
    support_15m = min(float(c[3]) for c in k15[-5:])
    resistance_15m = max(float(c[2]) for c in k15[-5:])
    support_1h = min(float(c[3]) for c in k60[-5:])
    resistance_1h = max(float(c[2]) for c in k60[-5:])

    row: dict[str, Any] = {
        'symbol': sym,
        'category': categorize_symbol(sym),
        'price': price,
        'trend_5m': trend_direction(k5),
        'trend_15m': trend_direction(k15),
        'trend_1h': trend_direction(k60),
        'trend_4h': trend_direction(k240),
        'pct5m': 100 * (close5[-1] / close5[-2] - 1) if len(close5) > 1 else 0,
        'pct15': 100 * (close15[-1] / close15[-2] - 1) if len(close15) > 1 else 0,
        'pct1h': 100 * (close60[-1] / close60[-2] - 1) if len(close60) > 1 else 0,
        'pct4h': 100 * (close240[-1] / close240[-2] - 1) if len(close240) > 1 else 0,
        'atr5': atr(k5),
        'atr15': atr(k15),
        'atr1h': atr(k60),
        'atr4h': atr(k240),
        'vol_spike': vol_spike,
        'avg_vol15': statistics.mean(vol15),
        'funding': funding_rate,
        'funding_time': int(funding_ts) if funding_ts else None,
        'oi': oi,
        'oi_notional': oi * price,
        'spread': best_ask - best_bid,
        'spread_pct': (best_ask - best_bid) / price if price else 0.0,
        'ask_bid_imbalance': ask_bid_imbalance,
        'quote_volume': float(t['quoteVolume']),
        'fresh_5m': candle_fresh(k5, '5m'),
        'fresh_15m': candle_fresh(k15, '15m'),
        'fresh_1h': candle_fresh(k60, '1h'),
        'fresh_4h': candle_fresh(k240, '4h'),
        'support_5m': min(float(c[3]) for c in k5[-5:]),
        'resistance_5m': max(float(c[2]) for c in k5[-5:]),
        'support_15m': support_15m,
        'resistance_15m': resistance_15m,
        'support_1h': support_1h,
        'resistance_1h': resistance_1h,
    }

    row['score'] = score_pair(row)
    return row


def scan_universe() -> list[dict[str, Any]]:
    """Fetch all Bybit linear perp tickers and filter to tradeable USDT pairs.

    Returns a list of dicts with keys: 'symbol' (flat format), 'lastPrice', 'quoteVolume'.
    """
    exchange = _get_exchange()
    tickers_raw = exchange.fetch_tickers()

    pairs: list[dict[str, Any]] = []
    for ccxt_sym, ticker in tickers_raw.items():
        # Only consider linear USDT perpetuals
        if not ccxt_sym.endswith(':USDT'):
            continue
        flat_sym = _from_ccxt_symbol(ccxt_sym)
        if not SYMBOL_RE.match(flat_sym):
            continue
        if 'DOWN' in flat_sym or 'UP' in flat_sym:
            continue

        last_price = float(ticker.get('last') or 0)
        quote_volume = float(ticker.get('quoteVolume') or 0)

        if quote_volume < cfg.scanner.min_quote_volume:
            continue
        if last_price < cfg.scanner.min_price_usdt:
            continue

        pairs.append({
            'symbol': flat_sym,
            'lastPrice': last_price,
            'quoteVolume': quote_volume,
        })

    pairs.sort(key=lambda x: x['quoteVolume'], reverse=True)
    return pairs[:cfg.scanner.scan_limit]


def select_top_candidates(rows: list[dict[str, Any]], max_candidates: int = 15) -> list[dict[str, Any]]:
    """Select top N candidates sorted by score descending."""
    return sorted(rows, key=lambda x: x['score'], reverse=True)[:max_candidates]


def _build_and_filter(t: dict[str, Any]) -> dict[str, Any] | None:
    """Build candidate row and apply minimum filters."""
    try:
        row = build_candidate_row(t)
        if not row:
            return None
        if row['oi_notional'] < cfg.scanner.min_oi_notional or row['quote_volume'] < cfg.scanner.min_quote_volume or row['vol_spike'] < cfg.scanner.min_vol_spike:
            return None
        return row
    except Exception as exc:
        logger.debug("build_and_filter failed for %s: %s", t.get('symbol', '?'), exc)
        return None


def scan_market(max_workers: int | None = None) -> list[dict[str, Any]]:
    """Scan the full Bybit linear perp universe and return scored candidates.

    Uses ThreadPoolExecutor for parallel candidate building.
    """
    pairs = scan_universe()
    rows: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max_workers or cfg.scanner.scan_workers) as pool:
        futures = {pool.submit(_build_and_filter, t): t for t in pairs}
        for future in as_completed(futures):
            row = future.result()
            if row:
                rows.append(row)
    return sorted(rows, key=lambda x: x['score'], reverse=True)


def score_pair(row: dict[str, Any]) -> float:
    """Score a candidate pair based on multiple factors. Returns float score."""
    s = cfg.scoring
    score = 0.0
    fresh_count = row['fresh_15m'] + row['fresh_1h'] + row['fresh_4h']
    score += fresh_count * s.fresh_weight

    if row['vol_spike'] >= s.vol_spike_high_threshold:
        score += min(24, (row['vol_spike'] - 1.0) * s.vol_spike_high_mult)
    elif row['vol_spike'] >= cfg.scanner.min_vol_spike:
        score += s.vol_spike_base_bonus
    else:
        score += s.vol_spike_penalty

    oi_notional = row['oi_notional']
    if oi_notional >= s.oi_tier_high:
        score += 30
    elif oi_notional >= s.oi_tier_mid:
        score += 22
    elif oi_notional >= cfg.scanner.min_oi_notional:
        score += 12
    else:
        score += s.oi_penalty

    capital_flow_bonus = min(s.oi_capital_flow_max, max(0.0, (oi_notional / 100_000_000) - 0.4) * 8)
    score += capital_flow_bonus

    if row['quote_volume'] >= s.qv_tier_high:
        score += 14
    elif row['quote_volume'] >= s.qv_tier_mid:
        score += 10
    elif row['quote_volume'] >= cfg.scanner.min_quote_volume:
        score += 6
    else:
        score += s.qv_penalty

    spread_pct = row.get('spread_pct', (row['spread'] / row['price']) if row['price'] else 0.0)
    score -= min(12, spread_pct * s.spread_mult)
    score += s.spread_wide_penalty if spread_pct > 0.002 else 0

    if row['price'] < 0.02:
        score += s.low_price_penalty_02
    elif row['price'] < 0.05:
        score += s.low_price_penalty_05

    imbalance = row['ask_bid_imbalance']
    if row['trend_4h'] == 'bullish':
        score += min(s.imbalance_max_bonus, max(0.0, 1.0 / max(imbalance, 0.01) - 1.0) * 12)
    else:
        score += min(s.imbalance_max_bonus, max(0.0, imbalance - 1.0) * 12)

    if oi_notional < cfg.scanner.min_oi_notional:
        score += s.oi_small_penalty
    if row['quote_volume'] < cfg.scanner.min_quote_volume:
        score += s.qv_small_penalty

    same_trend = len({row['trend_4h'], row['trend_1h'], row['trend_15m']})
    if same_trend == 1:
        score += s.trend_all_same_bonus
    elif same_trend == 2:
        score += s.trend_two_same_bonus
    else:
        score += s.trend_all_diff_penalty

    funding_support = row['funding']
    if row['trend_4h'] == 'bullish':
        score += s.funding_align_bonus if funding_support > 0 else s.funding_anti_penalty
    else:
        score += s.funding_align_bonus if funding_support < 0 else s.funding_anti_penalty

    if row['pct4h'] and ((row['pct4h'] > 0) == (row['trend_4h'] == 'bullish')):
        score += s.pct4h_align_bonus
    else:
        score += s.pct4h_anti_penalty
    if row['pct1h'] and ((row['pct1h'] > 0) == (row['trend_1h'] == 'bullish')):
        score += s.pct1h_align_bonus
    else:
        score += s.pct1h_anti_penalty

    score += s.pct_cross_bonus if row['pct4h'] * row['pct15'] > 0 else s.pct_cross_penalty
    return score


def main() -> None:
    """Run a full market scan and print results."""
    rows = scan_market()
    macro = get_macro_context(rows)

    print('TIME', datetime.now(timezone.utc).isoformat())
    print('SOURCE: Bybit Linear Perpetuals')
    print('MACRO CONTEXT:')
    print(macro['summary'])
    print('EVENTS:', macro['events_text'])
    print()
    print('TOP 12 candidates by score: symbol,score,vol_spike,oi_notional_millions,funding,imbalance,trend15m,trend1h,trend4h')
    for row in rows[:12]:
        print(
            f"{row['symbol']},{row['score']:.1f},{row['vol_spike']:.2f},{row['oi_notional'] / 1e6:.2f},{row['funding']:.6f},{row['ask_bid_imbalance']:.2f},{row['trend_15m']},{row['trend_1h']},{row['trend_4h']}"
        )

    print('\nDETAILED SHORTLIST')
    for row in rows[:8]:
        print('\n---')
        print(f"PAIR: {row['symbol']}")
        print(f"PRICE: {row['price']}")
        print(f"TRENDS: 4h={row['trend_4h']} 1h={row['trend_1h']} 15m={row['trend_15m']}")
        print(f"VOL SPIKE: {row['vol_spike']:.2f}")
        print(f"OI: {row['oi']:.0f}")
        print(f"FUNDING: {row['funding']:.6f}")
        print(f"ASK/BID IMBALANCE: {row['ask_bid_imbalance']:.2f}")
        print(f"ATR15: {row['atr15']:.4f} ATR1h: {row['atr1h']:.4f}")
        print(f"SCORE: {row['score']:.1f}")


if __name__ == '__main__':
    main()
