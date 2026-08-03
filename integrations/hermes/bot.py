import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

from config_loader import cfg
from deep_binance_analysis import get_cached_scan
from directional_binance_agents import (
    LongAgent, ShortAgent, SpotAgent, ArbAgent,
    DEFAULT_ACCOUNT_USDT,
)
from exchange_prices import get_price, get_order_book

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(message)s",
    filename=Path(__file__).parent / "logs" / "bot.log",
    encoding="utf-8",
)

API_BASE = "https://api.telegram.org/bot{token}"
POLL_INTERVAL = 5
AUTO_ALERT_INTERVAL = 3600

_dotenv_path = Path(__file__).parent / ".env"
if _dotenv_path.exists():
    with open(_dotenv_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID: int | None = None
_bot_start_ts = time.time()
_last_auto_ts: float = 0.0
_alerts_enabled = True

_known_commands = """
/scan — top candidates
/signals — all signals (intraday)
/ssg — scalp signals (tight stops, 15x)
/isg — intraday signals (5-10x, 1h structure)
/swg — swing signals (wide stops, 5x, 4h structure)
/combo — all modes combined
/spot — spot signals
/price SYM — current price (3 exchanges)
/funding SYM — funding rate
/depth SYM — order book imbalance
/brief SYM — trade brief
/perf SYM — signal performance for symbol
/regime — current market regime + historical stats
/config — show scoring parameters
/watchlist — alias for /scan
/status — system state
/evaluate — evaluation summary + trend
/alerts on|off — toggle auto alerts
/help — this message
"""


def _api(method: str, payload: dict | None = None) -> dict[str, Any] | None:
    if not BOT_TOKEN:
        return None
    try:
        r = requests.post(
            API_BASE.format(token=BOT_TOKEN) + f"/{method}",
            json=payload or {},
            timeout=10,
        )
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        logger.warning("telegram api error %s: %s", method, exc)
        return None


def send_message(text: str, chat_id: int | None = None) -> None:
    cid = chat_id or CHAT_ID
    if not cid or not BOT_TOKEN:
        return
    _api("sendMessage", {"chat_id": cid, "text": text, "parse_mode": "HTML"})


def _cmd_start(chat_id: int) -> None:
    global CHAT_ID
    CHAT_ID = chat_id
    send_message(
        f"Hermes Foundation active.\n{_known_commands}", chat_id=chat_id
    )


def _cmd_scan() -> str:
    rows, macro = get_cached_scan()
    rows = rows[:10]
    if not rows:
        return "No candidates."
    lines = [
        f"<b>MACRO:</b> {macro.get('summary', '')}",
        "",
        "<b>TOP 10:</b>",
        "sym score vs OI$M fund trend4h",
    ]
    for r in rows:
        lines.append(
            f"{r['symbol']} {r['score']:.0f} {r['vol_spike']:.1f}x "
            f"{r['oi_notional']/1e6:.0f} {r['funding']:.4f}% {r['trend_4h']}"
        )
    return "\n".join(lines)


def _cmd_signals() -> str:
    rows, macro = get_cached_scan()
    if not rows:
        return "No market data."

    agents: dict[str, Any] = {
        "LONG": LongAgent(),
        "SHORT": ShortAgent(),
        "SPOT": SpotAgent(),
        "ARB": ArbAgent(),
    }

    out = [f"<b>Signals — {macro.get('regime', '?')}</b>", ""]
    any_signal = False
    for name, agent in agents.items():
        sigs = agent.evaluate(rows, macro, account_usdt=DEFAULT_ACCOUNT_USDT)
        if not sigs:
            continue
        any_signal = True
        for s in sigs[:3]:
            rr = s.get("rr1", 0) or 0
            out.append(
                f"{s['symbol']} {s['direction']} "
                f"entry={s['entry_low']:.6f} stop={s['stop']:.6f} "
                f"tp1={s['tp1']:.6f} rr={rr:.1f}"
            )
        out.append("")

    if not any_signal:
        out.append("No actionable signals.")
    return "\n".join(out)


def _format_signal(s: dict[str, Any]) -> str:
    alloc = s.get("allocation_pcts", [])
    tp1_a = f" ({alloc[0]}%)" if len(alloc) > 0 else ""
    tp2_a = f" ({alloc[1]}%)" if len(alloc) > 1 else ""
    tp3_a = f" ({alloc[2]}%)" if len(alloc) > 2 else ""
    return (
        f"{s['symbol']} {s['direction']} mode={s.get('mode','')}\n"
        f"entry={s['entry_low']:.6f} stop={s['stop']:.6f}\n"
        f"TP1={s['tp1']:.6f}{tp1_a} TP2={s['tp2']:.6f}{tp2_a} TP3={s['tp3']:.6f}{tp3_a}\n"
        f"R:R={s.get('rr1',0):.1f}/{s.get('rr2',0):.1f}/{s.get('rr3',0):.1f} "
        f"risk={s.get('risk_amount',0):.0f}$"
    )


def _signals_for_mode(mode: str, label: str) -> str:
    rows, macro = get_cached_scan()
    if not rows:
        return "No market data."
    agents: dict[str, Any] = {
        "LONG": LongAgent(mode=mode),
        "SHORT": ShortAgent(mode=mode),
    }
    out = [f"<b>{label}</b>", ""]
    any_sig = False
    for name, agent in agents.items():
        sigs = agent.evaluate(rows, macro, account_usdt=DEFAULT_ACCOUNT_USDT)
        if not sigs:
            continue
        any_sig = True
        for s in sigs[:3]:
            out.append(_format_signal(s))
            out.append("")
    if not any_sig:
        out.append("No signals.")
    return "\n".join(out)


def _cmd_perf(symbol: str) -> str:
    from evaluate_signals import load_log, summarise_group

    records = load_log()
    matching = [r for r in records if r.get("symbol") == symbol]
    if not matching:
        return f"No signals for {symbol}."
    closed = [r for r in matching if r.get("outcome") and r["outcome"] not in ("OPEN", None)]
    total = len(matching)
    summary = summarise_group(symbol, matching)
    if not summary or summary["closed"] == 0:
        return f"{symbol}: {total} signals, none closed yet."
    return (
        f"<b>{symbol}</b> ({total} signals, {summary['closed']} closed)\n"
        f"WR={summary['winrate_pct']}% E={summary['expectancy_R']}R PF={summary['profit_factor']}\n"
        f"TP={summary['tp1_hits']} SL={summary['sl_hits']} EXP={summary['expired']}\n"
        f"Avg hold: {summary['avg_hold_bars']} bars"
    )


def _cmd_regime() -> str:
    _, macro = get_cached_scan()
    out = [f"<b>Regime: {macro.get('regime', '?')}</b>"]
    if macro.get("summary"):
        out.append(macro["summary"])
    if macro.get("events_text"):
        out.append(f"Events: {macro['events_text']}")

    from evaluate_signals import load_metrics_history
    history = load_metrics_history(limit=30)
    if history:
        regime_groups: dict[str, list[float]] = {}
        for s in history:
            r = s.get("regime", "unknown")
            regime_groups.setdefault(r, []).append(s["winrate_pct"])
        out.append("")
        out.append("<b>WR by regime:</b>")
        for regime, wrs in sorted(regime_groups.items(), key=lambda x: -len(x[1])):
            avg = sum(wrs) / len(wrs)
            out.append(f"{regime[:20]:<20} {avg:.1f}% ({len(wrs)} snapshots)")
    return "\n".join(out)


def _cmd_config() -> str:
    from config_loader import cfg as c
    out = [
        "<b>Scanner</b>",
        f"scan_limit={c.scanner.scan_limit} workers={c.scanner.scan_workers}",
        f"min_vol={c.scanner.min_vol_spike} min_oi={c.scanner.min_oi_notional/1e6:.0f}M",
        "",
        "<b>Scoring</b>",
        f"fresh_w={c.scoring.fresh_weight} trend_same={c.scoring.trend_all_same_bonus}",
        f"oi_high={c.scoring.oi_tier_high/1e6:.0f}M qv_high={c.scoring.qv_tier_high/1e6:.0f}M",
        "",
        "<b>Modes</b>",
    ]
    for m in ("scalp", "intraday", "swing"):
        mc = getattr(c.trading_modes, m, None)
        if mc:
            out.append(f"{m}: atr={mc.atr_tf} stop={mc.stop_atr_mult}x tp3={mc.tp3_atr_mult}x lev={mc.leverage}x")
    return "\n".join(out)


def _cmd_price(symbol: str) -> str:
    prices = []
    for ex in ("binance", "bybit", "mexc"):
        p = get_price(ex, symbol)
        if p is not None:
            prices.append(f"{ex}: {p:.4f}")
    if not prices:
        return f"No price data for {symbol}."
    return f"<b>{symbol}</b>\n" + "\n".join(prices)


def _cmd_funding(symbol: str) -> str:
    try:
        r = requests.get(
            "https://fapi.binance.com/fapi/v1/fundingRate",
            {"symbol": symbol, "limit": 3},
            timeout=10,
        )
        data = r.json()
        if not data:
            return f"No funding data for {symbol}."
        lines = [f"<b>{symbol} funding</b>"]
        for entry in reversed(data[-3:]):
            rate = float(entry["fundingRate"])
            ts = datetime.fromtimestamp(entry["fundingTime"] / 1000, tz=timezone.utc)
            lines.append(f"{ts.strftime('%m-%d %H:%M')}: {rate*100:.4f}%")
        return "\n".join(lines)
    except Exception as exc:
        return f"Funding error: {exc}"


def _cmd_depth(symbol: str) -> str:
    book = get_order_book("binance", symbol, limit=20)
    if not book:
        return f"No order book for {symbol}."
    bid_sum = sum(q for _, q in book["bids"][:10])
    ask_sum = sum(q for _, q in book["asks"][:10])
    imbalance = ask_sum / bid_sum if bid_sum else float("inf")
    best_bid = book["bids"][0][0] if book["bids"] else 0
    best_ask = book["asks"][0][0] if book["asks"] else 0
    spread = best_ask - best_bid
    spread_pct = spread / best_bid * 100 if best_bid else 0
    return (
        f"<b>{symbol} depth</b>\n"
        f"Bid: {best_bid:.6f} ({bid_sum:.2f})\n"
        f"Ask: {best_ask:.6f} ({ask_sum:.2f})\n"
        f"Spread: {spread:.6f} ({spread_pct:.3f}%)\n"
        f"Imbalance: {imbalance:.2f}"
    )


def _cmd_status() -> str:
    uptime_sec = time.time() - _bot_start_ts
    hours = int(uptime_sec // 3600)
    mins = int((uptime_sec % 3600) // 60)
    log_dir = Path(__file__).parent / "logs"
    log_files = sorted(log_dir.glob("agents_*.log")) if log_dir.exists() else []
    last_log = ""
    if log_files:
        last = log_files[-1]
        last_log = f"Last scan: {last.stem.replace('agents_', '')}"

    signal_path = Path(__file__).parent / "signals_log.jsonl"
    signal_count = 0
    if signal_path.exists():
        signal_count = len(signal_path.read_text(encoding="utf-8").strip().split("\n"))

    return (
        f"<b>Hermes Status</b>\n"
        f"Bot uptime: {hours}h {mins}m\n"
        f"Alerts: {'ON' if _alerts_enabled else 'OFF'}\n"
        f"{last_log}\n"
        f"Total signals: {signal_count}\n"
        f"Scan interval: hourly"
    )


def _cmd_brief(symbol: str) -> str:
    try:
        import io
        from contextlib import redirect_stdout
        from trade_brief import print_brief

        buf = io.StringIO()
        with redirect_stdout(buf):
            print_brief(symbol)
        text = buf.getvalue()
        return f"<pre>{text[:3000]}</pre>"
    except Exception as exc:
        return f"Brief failed: {exc}"


def _cmd_evaluate() -> str:
    from evaluate_signals import load_log, summarise_group, load_metrics_history

    records = load_log()
    closed = []
    if records:
        closed = [
            r for r in records
            if r.get("outcome") and r["outcome"] not in ("OPEN", None, "DATA_ERROR", "UNKNOWN_DIR")
        ]

    history = load_metrics_history(limit=14)
    lines = []

    if history:
        last = history[-1]
        lines.append(
            f"<b>Current</b> WR={last['winrate_pct']}% "
            f"E={last['expectancy_R']}R PF={last['profit_factor']} "
            f"closed={last['closed']}"
        )
        if len(history) >= 3:
            recent_wr = [s["winrate_pct"] for s in history[-3:]]
            avg_wr = sum(recent_wr) / len(recent_wr)
            lines.append(f"3-snapshot avg WR: {avg_wr:.1f}%")
        lines.append("")
        lines.append("<b>Trend (last 14):</b>")
        lines.append("date WR% E(R) PF")
        for s in history[-7:]:
            lines.append(
                f"{s['ts'][:10]} {s['winrate_pct']:.1f} {s['expectancy_R']:.2f} {s['profit_factor']:.2f}"
            )
    elif closed:
        overall = summarise_group("", closed)
        if overall:
            lines.append(
                f"<b>Evaluation</b> ({overall['closed']} closed)\n"
                f"WR={overall['winrate_pct']}% E={overall['expectancy_R']}R "
                f"PF={overall['profit_factor']}"
            )
    else:
        lines.append("No evaluated signals yet.")

    total_signals = len(records) if records else 0
    lines.append("")
    lines.append(f"Total in log: {total_signals}")

    return "\n".join(lines) if lines else "No data."


def _cmd_alerts(args: str) -> str:
    global _alerts_enabled
    arg = args.strip().lower()
    if arg == "on":
        _alerts_enabled = True
        return "Auto alerts ON."
    if arg == "off":
        _alerts_enabled = False
        return "Auto alerts OFF."
    return f"Alerts: {'ON' if _alerts_enabled else 'OFF'}. Use /alerts on|off"


def _dispatch(text: str, chat_id: int) -> None:
    text = text.strip()
    if text == "/start":
        return _cmd_start(chat_id)
    if text in ("/scan", "/watchlist"):
        return send_message(_cmd_scan())
    if text == "/signals":
        return send_message(_cmd_signals())
    if text == "/ssg":
        return send_message(_signals_for_mode("scalp", "SCALP SIGNALS (15x, atr5)"))
    if text == "/isg":
        return send_message(_signals_for_mode("intraday", "INTRADAY SIGNALS (8x, atr15)"))
    if text == "/swg":
        return send_message(_signals_for_mode("swing", "SWING SIGNALS (5x, atr4h)"))
    if text == "/spot":
        return send_message(_cmd_spot_signals())
    if text == "/combo":
        return send_message(_cmd_combo())
    if text == "/evaluate":
        return send_message(_cmd_evaluate())
    if text == "/status":
        return send_message(_cmd_status())
    if text == "/regime":
        return send_message(_cmd_regime())
    if text == "/config":
        return send_message(_cmd_config())
    if text == "/help":
        return send_message(_known_commands)
    if text.startswith("/price "):
        return send_message(_cmd_price(text.split(" ", 1)[1].strip().upper()))
    if text.startswith("/funding "):
        return send_message(_cmd_funding(text.split(" ", 1)[1].strip().upper()))
    if text.startswith("/depth "):
        return send_message(_cmd_depth(text.split(" ", 1)[1].strip().upper()))
    if text.startswith("/brief "):
        return send_message(_cmd_brief(text.split(" ", 1)[1].strip().upper()))
    if text.startswith("/perf "):
        return send_message(_cmd_perf(text.split(" ", 1)[1].strip().upper()))
    if text.startswith("/alerts"):
        return send_message(_cmd_alerts(text[7:]))
    if text.startswith("/"):
        return send_message(f"Unknown: {text}\n{_known_commands}")


def _cmd_spot_signals() -> str:
    rows, macro = get_cached_scan()
    if not rows:
        return "No market data."
    agent = SpotAgent()
    sigs = agent.evaluate(rows, macro, account_usdt=DEFAULT_ACCOUNT_USDT)
    if not sigs:
        return "No spot signals."
    out = [f"<b>SPOT SIGNALS — {macro.get('regime', '?')}</b>", ""]
    for s in sigs[:3]:
        out.append(_format_signal(s))
        out.append("")
    return "\n".join(out)


def _cmd_combo() -> str:
    rows, macro = get_cached_scan()
    if not rows:
        return "No market data."
    out = [f"<b>COMBO — {macro.get('regime', '?')}</b>", ""]
    for mode, label in [("scalp", "SCALP"), ("intraday", "INTRADAY"), ("swing", "SWING")]:
        agents = {"L": LongAgent(mode=mode), "S": ShortAgent(mode=mode)}
        out.append(f"<b>{label}</b>")
        any_sig = False
        for name, agent in agents.items():
            sigs = agent.evaluate(rows, macro, account_usdt=DEFAULT_ACCOUNT_USDT)
            for s in sigs[:2]:
                any_sig = True
                out.append(
                    f"{s['symbol']} {s['direction']} "
                    f"entry={s['entry_low']:.4f} stop={s['stop']:.4f} "
                    f"R={s.get('rr1',0):.1f}/{s.get('rr2',0):.1f}"
                )
        if not any_sig:
            out.append("no signals")
        out.append("")
    spot_agent = SpotAgent()
    spot_sigs = spot_agent.evaluate(rows, macro, account_usdt=DEFAULT_ACCOUNT_USDT)
    if spot_sigs:
        out.append("<b>SPOT</b>")
        for s in spot_sigs[:2]:
            out.append(f"{s['symbol']} entry={s['entry_low']:.4f} stop={s['stop']:.4f}")
    return "\n".join(out)


def _auto_alert() -> None:
    global _last_auto_ts
    if not _alerts_enabled:
        return
    now = time.time()
    if now - _last_auto_ts < AUTO_ALERT_INTERVAL:
        return
    _last_auto_ts = now

    text = _cmd_signals()
    if "No actionable" not in text:
        send_message(text)

    from evaluate_signals import load_metrics_history
    history = load_metrics_history(limit=5)
    if len(history) >= 3:
        recent = [s["winrate_pct"] for s in history[-3:]]
        avg = sum(recent) / len(recent)
        if avg < 45:
            send_message(
                f"<b>Quality alert</b>\n"
                f"3-snapshot avg WR: {avg:.1f}% (threshold: 45%)\n"
                f"Check: /evaluate"
            )


def poll() -> None:
    offset = 0
    while True:
        try:
            updates = _api("getUpdates", {"offset": offset, "timeout": 30})
            if updates and updates.get("ok") and updates.get("result"):
                for upd in updates["result"]:
                    offset = upd["update_id"] + 1
                    msg = upd.get("message") or upd.get("callback_query", {}).get("message", {})
                    text = msg.get("text", "")
                    cid = msg.get("chat", {}).get("id")
                    if cid:
                        _dispatch(text, cid)
            _auto_alert()
            time.sleep(POLL_INTERVAL)
        except KeyboardInterrupt:
            break
        except Exception as exc:
            logger.debug("poll error: %s", exc)
            time.sleep(POLL_INTERVAL * 2)


def main() -> None:
    if not BOT_TOKEN:
        print("Set TELEGRAM_BOT_TOKEN env var")
        return
    print(f"Bot polling... chat_id={CHAT_ID}")
    poll()


if __name__ == "__main__":
    main()
