"""Moteur de backtest réaliste multi-actifs.

Règles d'exécution (mission §7, ARCHITECTURE.md) :
- les poids cibles décidés à la clôture de la bougie t deviennent effectifs à
  l'**open de t+1** (``weights.shift(1)``) — jamais sur la même bougie ;
- coûts = turnover × (frais taker + slippage) appliqués au moment du rebalancement ;
- long-only, positions fractionnaires, **pas de levier** : l'exposition brute est
  plafonnée à 1 (le surplus est réduit proportionnellement) ;
- le cash ne rapporte rien.

Convention temporelle : l'equity indicée t est mesurée à l'open de la bougie t,
après paiement des coûts de rebalancement de t. Le rendement de la période t
(open t → open t+1) est crédité à t+1.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.utils.config import FeesConfig, SlippageConfig


@dataclass(frozen=True)
class CostModel:
    """Coût proportionnel par unité de turnover (aller simple)."""

    fee_rate: float
    slippage_rate: float

    @property
    def one_way(self) -> float:
        return self.fee_rate + self.slippage_rate

    @classmethod
    def from_configs(
        cls,
        fees: FeesConfig,
        slippage: SlippageConfig,
        fee_multiplier: float = 1.0,
        slippage_multiplier: float = 1.0,
    ) -> CostModel:
        return cls(
            fee_rate=fees.taker * fee_multiplier,
            slippage_rate=(slippage.base_bps / 10_000.0) * slippage_multiplier,
        )


@dataclass
class TradeEpisode:
    """Épisode de position sur un actif (poids > 0 continu)."""

    symbol: str
    entry_time: pd.Timestamp
    exit_time: pd.Timestamp
    bars_held: int
    pnl_pct_of_equity: float  # contribution nette approx., en fraction de l'equity


@dataclass
class BacktestResult:
    equity: pd.Series  # courbe d'equity (base 1.0), indexée à l'open de chaque bougie
    effective_weights: pd.DataFrame
    turnover: pd.Series
    costs_paid: pd.Series  # coûts par bougie, en fraction de l'equity
    trades: list[TradeEpisode]

    @property
    def total_cost_frac(self) -> float:
        return float(self.costs_paid.sum())


def _align(data: dict[str, pd.DataFrame], column: str) -> pd.DataFrame:
    """Aligne une colonne OHLCV de chaque actif sur l'union des index."""
    return pd.DataFrame({sym: df[column] for sym, df in data.items()}).sort_index()


def run_backtest(
    data: dict[str, pd.DataFrame],
    target_weights: pd.DataFrame,
    cost_model: CostModel,
    max_gross_exposure: float = 1.0,
) -> BacktestResult:
    """Exécute le backtest.

    Args:
        data: {symbol: OHLCV} — bougies clôturées, index UTC croissant.
        target_weights: poids cibles décidés à la clôture de chaque bougie
            (index temps, colonnes symboles, valeurs ∈ [0, 1]).
        cost_model: coûts proportionnels (frais + slippage).
        max_gross_exposure: plafond d'exposition brute (1.0 = pas de levier).

    Returns:
        BacktestResult (equity base 1.0, poids effectifs, turnover, coûts, trades).
    """
    opens = _align(data, "open")
    symbols = list(opens.columns)
    weights = target_weights.reindex(opens.index)[symbols].fillna(0.0).clip(lower=0.0)

    # Plafond d'exposition brute (pas de levier) : réduction proportionnelle.
    gross = weights.sum(axis=1)
    over = gross > max_gross_exposure
    if over.any():
        weights.loc[over] = weights.loc[over].div(gross[over], axis=0) * max_gross_exposure

    # ANTI-LOOKAHEAD : poids décidés en t -> effectifs à l'open de t+1.
    effective = weights.shift(1).fillna(0.0)

    # Un actif sans cotation à t ne peut pas être détenu (NaN open -> poids 0).
    effective = effective.where(opens.notna(), 0.0)

    # Rendement open->open de la période commençant à t : open[t+1]/open[t] - 1.
    ret_oo = opens.shift(-1).div(opens) - 1.0

    # Turnover au rebalancement de t (changement de poids exécuté à l'open de t).
    turnover = effective.diff().abs().sum(axis=1)
    turnover.iloc[0] = effective.iloc[0].abs().sum()
    cost_frac = turnover * cost_model.one_way

    # Contribution par actif et rendement de portefeuille par période.
    contrib = effective * ret_oo.fillna(0.0)
    period_ret = contrib.sum(axis=1)

    # equity[t] à l'open de t : coûts de t payés, puis rendement de la période t.
    growth = (1.0 - cost_frac) * (1.0 + period_ret)
    equity = growth.cumprod()

    # Épisodes de trade par actif (poids effectif > 0 continu).
    trades: list[TradeEpisode] = []
    cost_share = _cost_share(effective, cost_frac)
    for sym in symbols:
        w = effective[sym].to_numpy()
        net_contrib = (contrib[sym] - cost_share[sym]).to_numpy()
        holding = np.concatenate([[False], w > 0, [False]])
        starts = list(np.flatnonzero(~holding[:-1] & holding[1:]))
        ends = list(np.flatnonzero(holding[:-1] & ~holding[1:]))
        for s, e in zip(starts, ends, strict=True):
            trades.append(
                TradeEpisode(
                    symbol=sym,
                    entry_time=opens.index[s],
                    exit_time=opens.index[min(e, len(w) - 1)],
                    bars_held=e - s,
                    pnl_pct_of_equity=float(net_contrib[s:e].sum()),
                )
            )

    return BacktestResult(
        equity=equity,
        effective_weights=effective,
        turnover=turnover,
        costs_paid=cost_frac,
        trades=trades,
    )


def _cost_share(effective: pd.DataFrame, cost_frac: pd.Series) -> pd.DataFrame:
    """Répartit le coût de chaque rebalancement au prorata du |Δpoids| par actif."""
    dw = effective.diff().abs()
    dw.iloc[0] = effective.iloc[0].abs()
    total = dw.sum(axis=1).replace(0.0, np.nan)
    share = dw.div(total, axis=0).fillna(0.0)
    return share.mul(cost_frac, axis=0)
