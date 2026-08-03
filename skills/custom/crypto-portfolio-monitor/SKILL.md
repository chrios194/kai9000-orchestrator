---
name: crypto-portfolio-monitor
description: CRYPTO ORACLE enhanced. 6-layer analysis (Fundamentals, MTF TA, On-chain, Derivatives, Sentiment, Macro). Sovereign Signal format. Hermes Foundation integration. Liquidation alerts for XLM_PERP, aUSDT/XAUt.
---

# Crypto Portfolio Monitor — CRYPTO ORACLE Edition

## ZERO LAW
Truth > Agreement. Utility > Impression.
Не гадай. WAIT/NO TRADE при нехватке данных.

## TRIGGER
- Cron каждые 15 минут (XLM_PERP margin check)
- Cron 08:00 (morning briefing)
- On-demand: "проверь портфель", "рыночный режим", "сигналы"

## 6-LAYER ANALYSIS (CRYPTO ORACLE)
1. **Fundamentals** — токеномика (supply, unlock/vesting, utility, burn/staking), команда, инвесторы, roadmap
2. **MTF TA** — Elliott Wave, Wyckoff, SMC/ICT, Volume Profile, Market Structure (BOS/CHOCH/FVG/OB)
3. **On-chain** — активные адреса, SOPR, MVRV, NVT, стейкинг/TVL, карты ликвидаций
4. **Derivatives** — OI, funding, basis, orderbook, каскады ликвидаций
5. **Sentiment** — Fear & Greed, соцмедиа, нарративы, регуляторка, инфлюенсеры
6. **Macro** — DXY, ставки ФРС/ЕЦБ, геополитика, S&P/Nasdaq, глобальная ликвидность M2

## SOVEREIGN SIGNAL FORMAT
```
VERDICT: [STRONG LONG|LONG|NEUTRAL|SHORT|STRONG SHORT|WAIT|NO TRADE]
CONFIDENCE: [C:95+|C:80|C:60|C:40|C:?]
REGIME: [Bull Trend|Bear Trend|Range|Distribution|High Vol]
SYMBOL: [TICKER]
ENTRY ZONE: $XX - $XX
TP1: $XX | TP2: $XX | TP3: $XX
STOP LOSS: $XX — HARD INVALIDATION
R:R: 1:X | LEVERAGE: Xx | POSITION SIZE: X%
REASON: [ключевые факторы из 6-layer analysis]
INVALIDATION: [что убивает сетап]
```

## HERMES FOUNDATION INTEGRATION
- **LongAgent** → LONG signals (ATR-based entries, 3 TP levels)
- **ShortAgent** → SHORT signals
- **SpotAgent** → Spot signals (support-based stops)
- **ArbAgent** → Arbitrage (slippage, commission, depth aware)
- **MoonshotAgent** → Pre-pump scanner (x10+ candidates)
- **OptionsAgent** → IV monitoring (Deribit)

## CRITICAL MONITORING
| Asset | Trigger | Action |
|:--|:--|:--|
| aUSDT | Откат >0.5% от паритета $1 | CRITICAL ALERT → Telegram |
| XAUt | Отклонение >2% от цены золота | CRITICAL ALERT → Telegram |
| XLM_PERP | Маржа <15% | LIQUIDATION ALERT → Telegram + Push |

## RISK MANAGEMENT
- Max risk per trade: 0.5-2% capital
- Circuit breaker: 10-15% portfolio drawdown → STOP ALL TRADING
- Position size = (Capital × Max_risk) / (Entry - SL)
- Base leverage: 5-15x (scalp), 8x (intraday), 5x (swing)
- Move SL to breakeven after TP1

## RED TEAM (7 attacks, applies to each signal)
1. Logic — проверка рассуждений
2. Data — верификация источников
3. Context — полнота контекста
4. Counterparty — чьё мнение?
5. Time — актуальность данных
6. Scale — масштабируемость
7. First principles — фундаментальная проверка

## DATA SOURCES
- On-chain: Glassnode, Nansen, Dune, CryptoQuant, Santiment, Arkham, Token Terminal
- Market: TradingView, CMC, CoinGecko, Binance/Bybit/OKX, Coinglass, Hyblock
- Smart money: Whale Alert, DeBank, Lookonchain, Etherscan, 13F, ETF flows
- News: CryptoPanic, Twitter/X, Telegram, Reddit, official announcements

## WORKFLOW
1. `hermes_bridge.HermesBridge.get_signals()` → trading signals
2. `hermes_bridge.HermesBridge.get_market_regime()` → regime detection
3. `hermes_bridge.HermesBridge.check_liquidation_risk()` → margin alerts
4. Format as Sovereign Signal
5. RED TEAM audit on top 3 signals
6. Save to Obsidian vault + SQLite memory
7. If CRITICAL → send_notification()
