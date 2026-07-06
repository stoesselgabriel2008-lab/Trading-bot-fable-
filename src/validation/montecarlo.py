"""Monte Carlo par bootstrap des trades (Phase 6, étape 4).

Rééchantillonnage avec remise des PnL de trades OOS -> distributions du
rendement total et du drawdown, intervalles de confiance à 95 %.
(cf. RESEARCH.md §4 : ≥ 1000 tirages, 5000 pour des percentiles de DD fiables.)
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class MonteCarloResult:
    n_draws: int
    n_trades: int
    ret_mean: float
    ret_ci_low: float  # percentile 2,5 du rendement total
    ret_ci_high: float  # percentile 97,5
    dd_median: float
    dd_p95: float  # pire cas raisonnable : percentile 95 du max drawdown
    prob_negative: float  # P(rendement total < 0)


def bootstrap_trades(
    trade_pnls: list[float], n_draws: int = 2000, seed: int = 7
) -> MonteCarloResult | None:
    """Bootstrap des PnL de trades (fractions d'equity, approx. additives)."""
    pnls = np.asarray(trade_pnls, dtype=float)
    n = len(pnls)
    if n < 10:
        return None  # trop peu de trades pour une distribution qui veuille dire quelque chose
    rng = np.random.default_rng(seed)
    samples = rng.choice(pnls, size=(n_draws, n), replace=True)
    totals = samples.sum(axis=1)
    # max drawdown de chaque trajectoire cumulée (approximation additive)
    cum = np.cumsum(samples, axis=1)
    peaks = np.maximum.accumulate(cum, axis=1)
    dds = (cum - peaks).min(axis=1)
    return MonteCarloResult(
        n_draws=n_draws,
        n_trades=n,
        ret_mean=float(totals.mean()),
        ret_ci_low=float(np.percentile(totals, 2.5)),
        ret_ci_high=float(np.percentile(totals, 97.5)),
        dd_median=float(np.percentile(dds, 50)),
        dd_p95=float(np.percentile(dds, 5)),  # 5e percentile = pire 5 % (valeurs négatives)
        prob_negative=float((totals < 0).mean()),
    )
