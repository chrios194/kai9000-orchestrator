"""
config_loader.py — загрузка и валидация config.yaml.

Использование:
  from config_loader import cfg
  min_oi = cfg.scanner.min_oi_notional
  risk_pct = cfg.risk.default_risk_pct
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

try:
    import yaml
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False

CONFIG_PATH = Path(__file__).parent / 'config.yaml'


@dataclass
class ScannerConfig:
    scan_limit: int = 80
    min_quote_volume: float = 30_000_000
    min_oi_notional: float = 40_000_000
    min_vol_spike: float = 0.25
    min_price_usdt: float = 0.01
    scan_workers: int = 8


@dataclass
class ScoringConfig:
    fresh_weight: float = 12
    vol_spike_high_threshold: float = 1.4
    vol_spike_high_mult: float = 12
    vol_spike_base_bonus: float = 8
    vol_spike_penalty: float = -18
    oi_tier_high: float = 500_000_000
    oi_tier_mid: float = 200_000_000
    oi_tier_low: float = 40_000_000
    oi_penalty: float = -26
    oi_capital_flow_max: float = 14
    qv_tier_high: float = 250_000_000
    qv_tier_mid: float = 150_000_000
    qv_tier_low: float = 30_000_000
    qv_penalty: float = -10
    spread_mult: float = 25000
    spread_wide_penalty: float = -6
    low_price_penalty_02: float = -12
    low_price_penalty_05: float = -6
    imbalance_max_bonus: float = 12
    oi_small_penalty: float = -10
    qv_small_penalty: float = -8
    trend_all_same_bonus: float = 30
    trend_two_same_bonus: float = 16
    trend_all_diff_penalty: float = -24
    funding_align_bonus: float = 14
    funding_anti_penalty: float = -12
    pct4h_align_bonus: float = 8
    pct4h_anti_penalty: float = -8
    pct1h_align_bonus: float = 6
    pct1h_anti_penalty: float = -6
    pct_cross_bonus: float = 10
    pct_cross_penalty: float = -8


@dataclass
class LongAgentConfig:
    min_bull_count: int = 2
    min_oi_notional: float = 45_000_000
    min_vol_spike: float = 1.1
    max_spread_pct: float = 0.003
    entry_atr_low: float = 0.15
    entry_atr_high: float = 0.45
    stop_atr_mult: float = 0.35
    tp1_atr_mult: float = 2.0
    tp1_rr_min: float = 1.6
    tp2_atr_mult: float = 3.0
    tp2_rr_min: float = 2.5
    tp3_atr_mult: float = 4.5
    allocation_pcts: list = field(default_factory=lambda: [50, 30, 20])


@dataclass
class ShortAgentConfig:
    min_bear_count: int = 2
    min_oi_notional: float = 40_000_000
    min_vol_spike: float = 1.1
    max_spread_pct: float = 0.003
    entry_atr_low: float = 0.15
    entry_atr_high: float = 0.45
    stop_atr_mult: float = 0.35
    tp1_atr_mult: float = 2.0
    tp1_rr_min: float = 1.6
    tp2_atr_mult: float = 3.0
    tp2_rr_min: float = 2.5
    tp3_atr_mult: float = 4.5
    allocation_pcts: list = field(default_factory=lambda: [50, 30, 20])


@dataclass
class SpotAgentConfig:
    min_quote_volume: float = 50_000_000
    max_spread_pct: float = 0.002
    stop_atr_mult: float = 1.5
    tp1_atr_mult: float = 1.8


@dataclass
class MoonshotAgentConfig:
    min_vol_spike: float = 3.0
    max_price: float = 5.0
    tp1_mult: float = 2.0
    tp2_mult: float = 4.0
    lookahead_bars: int = 96


@dataclass
class OptionsAgentConfig:
    underlyings: List[str] = field(default_factory=lambda: ['BTCUSDT', 'ETHUSDT'])
    funding_extreme: float = 0.0005
    move_extreme_pct: float = 8.0


@dataclass
class ArbAgentConfig:
    min_effective_profit: float = 0.004
    min_quote_volume: float = 5_000_000
    taker_fee_per_side: float = 0.0004
    cache_ttl_sec: float = 30


@dataclass
class AgentsConfig:
    long: LongAgentConfig = field(default_factory=LongAgentConfig)
    short: ShortAgentConfig = field(default_factory=ShortAgentConfig)
    spot: SpotAgentConfig = field(default_factory=SpotAgentConfig)
    moonshot: MoonshotAgentConfig = field(default_factory=MoonshotAgentConfig)
    options: OptionsAgentConfig = field(default_factory=OptionsAgentConfig)
    arb: ArbAgentConfig = field(default_factory=ArbAgentConfig)


@dataclass
class RiskConfig:
    default_account_usdt: float = 10_000
    default_risk_pct: float = 0.01
    default_leverage: int = 8
    spot_risk_pct: float = 0.005
    arb_risk_pct: float = 0.005
    moonshot_risk_pct: float = 0.002


@dataclass
class BacktestConfig:
    min_rr: float = 1.5
    max_hold_bars: int = 48
    lookback_days_default: int = 30


@dataclass
class TradingModeConfig:
    min_oi_notional: float = 40_000_000
    min_vol_spike: float = 1.1
    max_spread_pct: float = 0.003
    atr_tf: str = "atr15"
    entry_atr_low: float = 0.15
    entry_atr_high: float = 0.45
    stop_atr_mult: float = 0.35
    tp1_atr_mult: float = 2.0
    tp1_rr_min: float = 1.6
    tp2_atr_mult: float = 3.0
    tp2_rr_min: float = 2.5
    tp3_atr_mult: float = 4.5
    allocation_pcts: list = field(default_factory=lambda: [50, 30, 20])
    leverage: int = 8
    risk_pct: float = 0.01


@dataclass
class TradingModesConfig:
    scalp: TradingModeConfig = field(default_factory=TradingModeConfig)
    intraday: TradingModeConfig = field(default_factory=TradingModeConfig)
    swing: TradingModeConfig = field(default_factory=TradingModeConfig)


@dataclass
class ExchangeConfig:
    name: str = 'bybit'
    market_type: str = 'linear'
    testnet: bool = False


@dataclass
class AppConfig:
    exchange: ExchangeConfig = field(default_factory=ExchangeConfig)
    scanner: ScannerConfig = field(default_factory=ScannerConfig)
    scoring: ScoringConfig = field(default_factory=ScoringConfig)
    agents: AgentsConfig = field(default_factory=AgentsConfig)
    risk: RiskConfig = field(default_factory=RiskConfig)
    backtest: BacktestConfig = field(default_factory=BacktestConfig)
    trading_modes: TradingModesConfig = field(default_factory=TradingModesConfig)


def _populate(dc_instance, data: dict):
    """Рекурсивно заполняет dataclass из словаря (только известные поля)."""
    if not isinstance(data, dict):
        return dc_instance
    for fname, fval in data.items():
        if not hasattr(dc_instance, fname):
            continue
        cur = getattr(dc_instance, fname)
        if hasattr(cur, '__dataclass_fields__'):
            _populate(cur, fval)
        else:
            # strip underscores from numeric literals in YAML (e.g. 30_000_000)
            if isinstance(fval, str):
                try:
                    fval = int(fval.replace('_', ''))
                except ValueError:
                    try:
                        fval = float(fval.replace('_', ''))
                    except ValueError:
                        pass
            setattr(dc_instance, fname, fval)
    return dc_instance


def load_config(path=CONFIG_PATH) -> AppConfig:
    app = AppConfig()
    if not _YAML_AVAILABLE:
        return app  # use defaults silently
    if not Path(path).exists():
        return app
    try:
        with open(path, 'r', encoding='utf-8') as f:
            raw = yaml.safe_load(f) or {}
        _populate(app, raw)
    except Exception as e:
        print(f'[config_loader] Warning: could not load config.yaml: {e}. Using defaults.')
    return app


# Singleton — импортируй cfg везде
cfg: AppConfig = load_config()


if __name__ == '__main__':
    import json, dataclasses
    print(json.dumps(dataclasses.asdict(cfg), indent=2, default=str))
