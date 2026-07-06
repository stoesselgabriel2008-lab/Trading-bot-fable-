"""Classification des régimes de marché et analyse par régime (Phase 6, étape 6).

Règle simple et causale, définie À PARTIR des données (RESEARCH.md §4) :
- bear  : drawdown depuis le plus haut 1 an > 20 %
- bull  : close > SMA(200) et pas bear
- range : le reste
"""

from __future__ import annotations

import pandas as pd


def classify_regimes(
    close: pd.Series, sma_window: int = 200, dd_threshold: float = 0.20
) -> pd.Series:
    sma = close.rolling(sma_window).mean()
    rolling_peak = close.rolling(365, min_periods=1).max()
    dd = close / rolling_peak - 1.0
    regime = pd.Series("range", index=close.index)
    regime[dd < -dd_threshold] = "bear"
    regime[(close > sma) & (dd >= -dd_threshold)] = "bull"
    return regime


def returns_by_regime(strategy_returns: pd.Series, regimes: pd.Series) -> pd.DataFrame:
    """Rendement cumulé et nombre de bougies de la stratégie par régime."""
    aligned = regimes.reindex(strategy_returns.index).ffill()
    rows = []
    for reg in ("bull", "bear", "range"):
        rets = strategy_returns[aligned == reg]
        cum = float((1 + rets).prod() - 1) if len(rets) else 0.0
        rows.append({"regime": reg, "n_bars": len(rets), "cum_return": cum})
    return pd.DataFrame(rows).set_index("regime")
