import requests
from datetime import datetime, timezone


def safe_get(url, params=None, timeout=6):
    try:
        r = requests.get(url, params=params, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def get_deribit_iv(symbol):
    """Best-effort fetch of implied volatility from Deribit for given underlying symbol.

    Returns dict: {'underlying': symbol, 'iv_surface': {...}, 'atm_iv': float} or None
    """
    # Deribit uses instruments like BTC-PERP or option instruments; for simplicity, try to fetch index volatility
    try:
        idx = symbol.replace('USDT', '').upper()
        # Deribit index endpoint example (public): /api/v2/public/get_volatility_index_value
        url = f'https://www.deribit.com/api/v2/public/get_volatility_index_value'
        data = safe_get(url, {'currency': idx})
        if not data or 'result' not in data:
            return None
        atm_iv = data['result'].get('value')
        return {'underlying': idx, 'atm_iv': atm_iv}
    except Exception:
        return None


def get_options_iv(symbol):
    """Unified accessor for options IV. Tries multiple providers.

    Returns atm_iv (float) or None
    """
    # try deribit
    res = get_deribit_iv(symbol)
    if res and 'atm_iv' in res:
        return res['atm_iv']
    return None


if __name__ == '__main__':
    print('Options data helper')