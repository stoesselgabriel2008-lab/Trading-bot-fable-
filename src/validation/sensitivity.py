"""Sensibilité aux paramètres (Phase 6, étape 3).

Fait varier chaque paramètre de ±30 % autour de l'optimum retenu et mesure le
Sharpe. Une stratégie qui ne survit que sur un îlot étroit de paramètres = REJET
(critère : la MÉDIANE des voisins doit rester « du même monde » que l'optimum).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from src.backtest.engine import CostModel
from src.strategies.base import Strategy
from src.validation.walkforward import run_strategy

#: Variations relatives testées autour de l'optimum.
FACTORS = (0.7, 0.85, 1.0, 1.15, 1.3)


@dataclass
class SensitivityResult:
    base_sharpe: float
    grid: pd.DataFrame  # colonnes : param, factor, value, sharpe
    neighbor_median_sharpe: float
    is_robust: bool


def _vary(value: Any, factor: float, lo: float, hi: float) -> Any:
    out = value * factor
    if isinstance(value, int):
        rounded = round(out)
        rounded = max(int(lo), min(int(hi), rounded))
        return max(rounded, 1)
    return max(lo, min(hi, out))


def sensitivity_analysis(
    cls: type[Strategy],
    best_params: dict[str, Any],
    data: dict[str, pd.DataFrame],
    cost: CostModel,
    timeframe: str,
    robustness_floor: float = 0.5,
) -> SensitivityResult:
    """Sharpe de chaque voisin univarié (±15 %, ±30 %) de l'optimum.

    ``is_robust`` : la médiane des Sharpe voisins ≥ ``robustness_floor`` ×
    Sharpe optimal (et l'optimum > 0). Critère volontairement simple et écrit
    AVANT de voir les résultats (anti data-snooping).
    """
    base_metrics, _ = run_strategy(cls, best_params, data, cost, timeframe)
    rows = []
    for param, value in best_params.items():
        if param not in cls.param_space or isinstance(value, bool):
            continue
        lo, hi, _ = cls.param_space[param]
        for factor in FACTORS:
            if factor == 1.0:
                continue
            variant = dict(best_params)
            variant[param] = _vary(value, factor, lo, hi)
            if variant[param] == value:
                continue
            try:
                m, _ = run_strategy(cls, variant, data, cost, timeframe)
                sharpe = m.sharpe
            except (ValueError, KeyError):
                sharpe = float("nan")
            rows.append(
                {"param": param, "factor": factor, "value": variant[param], "sharpe": sharpe}
            )
    grid = pd.DataFrame(rows)
    neighbor_median = float(grid["sharpe"].median()) if not grid.empty else 0.0
    is_robust = bool(
        base_metrics.sharpe > 0 and neighbor_median >= robustness_floor * base_metrics.sharpe
    )
    return SensitivityResult(
        base_sharpe=base_metrics.sharpe,
        grid=grid,
        neighbor_median_sharpe=neighbor_median,
        is_robust=is_robust,
    )
