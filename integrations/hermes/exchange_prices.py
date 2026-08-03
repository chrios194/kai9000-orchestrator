import logging
from typing import Any

import ccxt

logger = logging.getLogger(__name__)

_EXCHANGES: dict[str, ccxt.Exchange] = {}
_FUTURES_SYMBOLS = {'binance', 'bybit', 'mexc'}


def _ccxt_name(name: str) -> str:
    mapping = {
        'binance': 'binanceusdm',
        'bybit': 'bybit',
        'mexc': 'mexc3',
    }
    return mapping.get(name.lower(), name.lower())


def _symbol(sym: str) -> str:
    if sym.endswith('USDT') and len(sym) > 4:
        return sym[:-4] + '/USDT'
    return sym.replace('_', '/')


def get_exchange(name: str) -> ccxt.Exchange | None:
    key = name.lower()
    if key in _EXCHANGES:
        return _EXCHANGES[key]
    cname = _ccxt_name(key)
    if not hasattr(ccxt, cname):
        logger.debug("unknown exchange: %s", name)
        return None
    try:
        ex_cls = getattr(ccxt, cname)
        ex = ex_cls({
            'enableRateLimit': True,
            'timeout': 30000,
        })
        if key in _FUTURES_SYMBOLS:
            ex.options['defaultType'] = 'swap'
        _EXCHANGES[key] = ex
        return ex
    except Exception as exc:
        logger.debug("init exchange %s failed: %s", name, exc)
        return None


def get_price(exchange: str, symbol: str) -> float | None:
    ex = get_exchange(exchange)
    if not ex:
        return None
    try:
        ticker = ex.fetch_ticker(_symbol(symbol))
        return float(ticker['last'])
    except Exception as exc:
        logger.debug("get_price %s %s: %s", exchange, symbol, exc)
        return None


def get_ticker(exchange: str, symbol: str) -> dict[str, Any] | None:
    ex = get_exchange(exchange)
    if not ex:
        return None
    try:
        return ex.fetch_ticker(_symbol(symbol))
    except Exception as exc:
        logger.debug("get_ticker %s %s: %s", exchange, symbol, exc)
        return None


def get_order_book(exchange: str, symbol: str, limit: int = 50) -> dict[str, Any] | None:
    ex = get_exchange(exchange)
    if not ex:
        return None
    try:
        book = ex.fetch_order_book(_symbol(symbol), limit=min(limit, 100))
        return {
            'bids': [(float(p), float(q)) for p, q in book['bids']],
            'asks': [(float(p), float(q)) for p, q in book['asks']],
        }
    except Exception as exc:
        logger.debug("get_order_book %s %s: %s", exchange, symbol, exc)
        return None


def estimate_slippage(levels: list[tuple[float, float]], qty_needed: float, reference_price: float | None = None) -> float | None:
    if not levels or qty_needed <= 0:
        return 0.0
    remaining = qty_needed
    accum_cost = 0.0
    accum_qty = 0.0
    for price, q in levels:
        take = min(remaining, q)
        accum_cost += take * price
        accum_qty += take
        remaining -= take
        if remaining <= 1e-12:
            break
    if remaining > 1e-6:
        return None
    avg_price = accum_cost / accum_qty if accum_qty > 0 else None
    if avg_price is None:
        return None
    ref = reference_price or levels[0][0]
    if ref == 0:
        return None
    return (avg_price - ref) / ref
