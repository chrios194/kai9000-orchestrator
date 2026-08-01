---
name: crypto-portfolio-monitor
description: Monitors cryptocurrency portfolio health, tracks depeg risks for stablecoins (aUSDT, XAUt), monitors perpetual futures margin (XLM_PERP), and generates alerts for liquidation threats. Use when checking portfolio status, margin requirements, or stablecoin peg stability.
---

# Crypto Portfolio Monitor

## Critical Assets to Track
Based on user's portfolio configuration:
- **aUSDT**: Pegged to USDT at ~$1. Alert if deviates >0.5% (below $0.995)
- **XAUt**: Pegged to gold. Alert if deviates >2% from spot gold price
- **XLM_PERP**: Perpetual futures on WhiteBIT. Monitor margin ratio; alert if below 15% (liquidation zone)

## Monitoring Protocol

### Step 1: Data Collection
Fetch current state via MCP servers:
- `binance-mcp`: Get spot prices for USDT, XAUt, XLM
- Check margin status via exchange API (WhiteBIT for XLM_PERP)
- Query on-chain data for aUSDT backing if available

### Step 2: Risk Assessment
For each asset calculate:
1. **Depeg risk**: |current_price - peg_price| / peg_price
2. **Margin health**: (equity / margin_used) * 100
3. **Liquidation distance**: (current_price - liquidation_price) / current_price * 100

### Step 3: Alert Generation
Alert tiers:
- **GREEN**: All assets within normal range. Log to daily brief.
- **YELLOW**: One or more assets approaching threshold (>80% of alert level). Recommend action.
- **RED**: Threshold breached. Immediate notification required.

### Step 4: Action Recommendations
- aUSDT depeg: Recommend exit to USDC or fiat
- XAUt depeg: Recommend conversion to physical gold or stablecoin
- XLM_PERP margin critical: Recommend either:
  A) Add 10-20% more collateral
  B) Reduce position size by 25-50%
  C) Close position entirely if trend is adverse

### Step 5: Output Format
```
PORTFOLIO HEALTH: [GREEN/YELLOW/RED]
├── aUSDT: $X.XXXX (peg: $1.00) → [OK/ALERT]
├── XAUt: $X.XXXX (gold spot: $X) → [OK/ALERT]
├── XLM_PERP: Margin XX% → [SAFE/WARNING/CRITICAL]
└── Recommended actions: [list]
```

## Integration
- Save daily snapshot to `vault/01 - Daily/{{date}}_crypto_brief.md`
- Trigger alert via Telegram notification channel
- Log to SQLite Memory Tree for historical tracking
