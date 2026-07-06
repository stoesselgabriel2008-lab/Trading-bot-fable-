"""Walk-forward rolling (Phase 6, étape 2).

Pour chaque fenêtre : recherche du meilleur jeu de paramètres sur l'IS
(critère : Sharpe), puis évaluation OOS sur la fenêtre suivante avec CES
paramètres. Les métriques agrégées ne proviennent QUE des segments OOS.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from src.backtest.engine import CostModel, run_backtest
from src.backtest.metrics import Metrics, compute_metrics
from src.strategies.base import Strategy


@dataclass
class WindowResult:
    is_start: pd.Timestamp
    oos_start: pd.Timestamp
    oos_end: pd.Timestamp
    best_params: dict[str, Any]
    is_sharpe: float
    oos_return: float
    oos_sharpe: float


@dataclass
class WalkForwardResult:
    windows: list[WindowResult]
    oos_returns: pd.Series  # rendements par bougie, concaténation des OOS
    oos_metrics: Metrics | None
    n_configs_tested: int  # comptage HONNÊTE de toutes les configurations
    trial_sharpes: list[float] = field(default_factory=list)  # SR de chaque essai IS
    oos_trade_pnls: list[float] = field(default_factory=list)  # PnL des trades OOS

    @property
    def pct_windows_positive(self) -> float:
        if not self.windows:
            return 0.0
        return sum(1 for w in self.windows if w.oos_return > 0) / len(self.windows)


def grid_from_presets(cls: type[Strategy]) -> list[dict[str, Any]]:
    """Grille de paramètres = presets + variations univariées autour du preset
    balanced (bornes de param_space). Volontairement petite : chaque configuration
    testée augmente le risque de data snooping et sera comptée dans le DSR."""
    grid: list[dict[str, Any]] = [dict(p) for p in cls.presets.values()]
    balanced = dict(cls.presets.get("balanced", {}))
    for key, (lo, hi, _default) in cls.param_space.items():
        if key not in balanced:
            continue
        for factor in (0.7, 1.3):
            variant = dict(balanced)
            base = balanced[key]
            value = base * factor
            if isinstance(base, int):
                value = round(max(lo, min(hi, value)))
                if value < 2 and key not in ("top_k",):
                    value = 2
            else:
                value = max(lo, min(hi, value))
            variant[key] = value
            if variant not in grid:
                grid.append(variant)
    # dédoublonnage
    unique: list[dict[str, Any]] = []
    for g in grid:
        if g not in unique:
            unique.append(g)
    return unique


def _slice(data: dict[str, pd.DataFrame], start, end) -> dict[str, pd.DataFrame]:
    return {k: df[(df.index >= start) & (df.index < end)] for k, df in data.items()}


def run_strategy(
    cls: type[Strategy],
    params: dict[str, Any],
    data: dict[str, pd.DataFrame],
    cost: CostModel,
    timeframe: str,
) -> tuple[Metrics, pd.Series]:
    strat = cls(name=cls.__name__, params=params)
    targets = strat.generate_targets(data)
    result = run_backtest(data, targets, cost)
    return compute_metrics(result, timeframe), result.equity.pct_change().fillna(0.0)


def walk_forward(
    cls: type[Strategy],
    data: dict[str, pd.DataFrame],
    cost: CostModel,
    timeframe: str,
    is_bars: int,
    oos_bars: int,
    grid: list[dict[str, Any]] | None = None,
) -> WalkForwardResult:
    """Walk-forward rolling sur le segment fourni (normalement : dev, 70 %)."""
    grid = grid if grid is not None else grid_from_presets(cls)
    longest = max(data.values(), key=len)
    idx = longest.index
    windows: list[WindowResult] = []
    oos_parts: list[pd.Series] = []
    trial_sharpes: list[float] = []
    oos_trade_pnls: list[float] = []
    n_configs = 0

    start = 0
    while start + is_bars + oos_bars <= len(idx):
        is_lo, is_hi = idx[start], idx[start + is_bars]
        oos_hi = idx[min(start + is_bars + oos_bars, len(idx) - 1)]
        is_data = _slice(data, is_lo, is_hi)
        oos_data = _slice(data, is_lo, oos_hi)  # inclut l'IS pour le warm-up…

        best_params, best_sharpe = None, -float("inf")
        for params in grid:
            n_configs += 1
            try:
                m, _ = run_strategy(cls, params, is_data, cost, timeframe)
            except (ValueError, KeyError):
                continue
            trial_sharpes.append(m.sharpe / (365**0.5))  # ordre de grandeur non annualisé
            if m.sharpe > best_sharpe:
                best_sharpe, best_params = m.sharpe, params

        if best_params is None:
            start += oos_bars
            continue

        # Évaluation OOS : warm-up sur l'IS mais métriques UNIQUEMENT sur l'OOS.
        strat = cls(name=cls.__name__, params=best_params)
        oos_bt = run_backtest(oos_data, strat.generate_targets(oos_data), cost)
        full_rets = oos_bt.equity.pct_change().fillna(0.0)
        oos_rets = full_rets[full_rets.index >= is_hi]
        oos_trade_pnls.extend(t.pnl_pct_of_equity for t in oos_bt.trades if t.entry_time >= is_hi)
        oos_return = float((1 + oos_rets).prod() - 1)
        std = oos_rets.std(ddof=1)
        oos_sharpe = float(oos_rets.mean() / std * (365**0.5)) if std and std > 0 else 0.0
        windows.append(
            WindowResult(
                is_start=is_lo,
                oos_start=is_hi,
                oos_end=oos_hi,
                best_params=best_params,
                is_sharpe=best_sharpe,
                oos_return=oos_return,
                oos_sharpe=oos_sharpe,
            )
        )
        oos_parts.append(oos_rets)
        start += oos_bars

    if oos_parts:
        oos_returns = pd.concat(oos_parts)
        oos_metrics = _metrics_from_returns(oos_returns, timeframe, oos_trade_pnls)
    else:
        oos_returns = pd.Series(dtype=float)
        oos_metrics = None

    return WalkForwardResult(
        windows=windows,
        oos_returns=oos_returns,
        oos_metrics=oos_metrics,
        n_configs_tested=n_configs,
        trial_sharpes=trial_sharpes,
        oos_trade_pnls=oos_trade_pnls,
    )


def _metrics_from_returns(
    returns: pd.Series, timeframe: str, trade_pnls: list[float] | None = None
) -> Metrics:
    """Métriques agrégées sur une série de rendements OOS concaténés."""
    import math

    from src.backtest.metrics import PERIODS_PER_YEAR, drawdown_stats
    from src.backtest.metrics import Metrics as M

    ppy = PERIODS_PER_YEAR[timeframe]
    equity = (1 + returns).cumprod()
    n = len(equity)
    total = float(equity.iloc[-1] - 1)
    ann = float(equity.iloc[-1] ** (ppy / n) - 1) if n else 0.0
    vol = float(returns.std(ddof=1)) * math.sqrt(ppy)
    sharpe = float(returns.mean()) * ppy / vol if vol > 0 else 0.0
    downside = returns[returns < 0]
    dvol = float(downside.std(ddof=1)) * math.sqrt(ppy) if len(downside) > 1 else 0.0
    sortino = float(returns.mean()) * ppy / dvol if dvol > 0 else 0.0
    max_dd, dd_dur = drawdown_stats(equity)
    calmar = ann / abs(max_dd) if max_dd < 0 else 0.0

    pnls = trade_pnls or []
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    pf = sum(wins) / abs(sum(losses)) if losses else (math.inf if wins else 0.0)
    win_rate = len(wins) / len(pnls) if pnls else 0.0
    expectancy = sum(pnls) / len(pnls) if pnls else 0.0

    return M(
        total_return=total,
        annualized_return=ann,
        annualized_volatility=vol,
        sharpe=sharpe,
        sortino=sortino,
        calmar=calmar,
        max_drawdown=max_dd,
        max_drawdown_duration_bars=dd_dur,
        profit_factor=pf,
        win_rate=win_rate,
        expectancy_per_trade=expectancy,
        avg_exposure=0.0,
        n_trades=len(pnls),
        total_turnover=0.0,
        total_costs_frac=0.0,
        n_bars=n,
    )
