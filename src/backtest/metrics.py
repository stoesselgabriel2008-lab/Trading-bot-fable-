"""Métriques de performance calculées sur un BacktestResult.

Toutes les métriques exigées par la mission (§7) : rendement total/annualisé,
volatilité, Sharpe, Sortino, Calmar, max drawdown + durée, profit factor,
win rate, expectancy par trade, exposition moyenne, nombre de trades, turnover,
frais cumulés.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

from src.backtest.engine import BacktestResult

#: Périodes par an selon le timeframe (marchés crypto : 24/7, 365 j).
PERIODS_PER_YEAR = {"1h": 24 * 365, "4h": 6 * 365, "1d": 365}


@dataclass(frozen=True)
class Metrics:
    total_return: float
    annualized_return: float
    annualized_volatility: float
    sharpe: float
    sortino: float
    calmar: float
    max_drawdown: float
    max_drawdown_duration_bars: int
    profit_factor: float
    win_rate: float
    expectancy_per_trade: float
    avg_exposure: float
    n_trades: int
    total_turnover: float
    total_costs_frac: float
    n_bars: int

    def to_dict(self) -> dict[str, float | int]:
        return asdict(self)


def compute_metrics(result: BacktestResult, timeframe: str) -> Metrics:
    """Calcule toutes les métriques d'un backtest."""
    ppy = PERIODS_PER_YEAR[timeframe]
    equity = result.equity.dropna()
    n = len(equity)
    if n < 2:
        raise ValueError("Equity curve trop courte pour calculer des métriques")

    returns = equity.pct_change().dropna()
    total_return = float(equity.iloc[-1] / equity.iloc[0] - 1.0)
    years = n / ppy
    annualized_return = float((equity.iloc[-1] / equity.iloc[0]) ** (1 / years) - 1.0)

    vol = float(returns.std(ddof=1)) * math.sqrt(ppy)
    mean_ann = float(returns.mean()) * ppy
    sharpe = mean_ann / vol if vol > 0 else 0.0

    downside = returns[returns < 0]
    downside_vol = float(downside.std(ddof=1)) * math.sqrt(ppy) if len(downside) > 1 else 0.0
    sortino = mean_ann / downside_vol if downside_vol > 0 else 0.0

    max_dd, dd_duration = drawdown_stats(equity)
    calmar = annualized_return / abs(max_dd) if max_dd < 0 else 0.0

    pnls = np.array([t.pnl_pct_of_equity for t in result.trades])
    n_trades = len(pnls)
    wins = pnls[pnls > 0]
    losses = pnls[pnls < 0]
    win_rate = float(len(wins) / n_trades) if n_trades else 0.0
    profit_factor = (
        float(wins.sum() / abs(losses.sum()))
        if losses.sum() < 0
        else (math.inf if len(wins) else 0.0)
    )
    expectancy = float(pnls.mean()) if n_trades else 0.0

    return Metrics(
        total_return=total_return,
        annualized_return=annualized_return,
        annualized_volatility=vol,
        sharpe=sharpe,
        sortino=sortino,
        calmar=calmar,
        max_drawdown=max_dd,
        max_drawdown_duration_bars=dd_duration,
        profit_factor=profit_factor,
        win_rate=win_rate,
        expectancy_per_trade=expectancy,
        avg_exposure=float(result.effective_weights.sum(axis=1).mean()),
        n_trades=n_trades,
        total_turnover=float(result.turnover.sum()),
        total_costs_frac=result.total_cost_frac,
        n_bars=n,
    )


def drawdown_stats(equity: pd.Series) -> tuple[float, int]:
    """Max drawdown (négatif) et durée max sous le plus haut précédent (en bougies)."""
    peak = equity.cummax()
    dd = equity / peak - 1.0
    max_dd = float(dd.min())
    under = dd < 0
    # Durée max d'une séquence continue sous l'ancien plus haut.
    longest = current = 0
    for flag in under:
        current = current + 1 if flag else 0
        longest = max(longest, current)
    return max_dd, longest
