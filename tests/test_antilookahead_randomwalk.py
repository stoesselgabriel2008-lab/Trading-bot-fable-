"""Test « random walk » (Phase 4, obligatoire) : sur du bruit pur, toute stratégie
doit rendre ≈ 0 avant frais et < 0 après frais. Un « gain » sur marche aléatoire
= bug de lookahead.

Inclut un CANARI : une stratégie qui triche (regarde t+1) doit être détectée
par ce même test — preuve que le test a du mordant.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from src.backtest.engine import CostModel, run_backtest

N_SEEDS = 40
N_BARS = 1500
SIGMA = 0.02  # volatilité par bougie


def random_walk_ohlcv(seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    log_steps = rng.normal(0.0, SIGMA, N_BARS)  # AUCUNE dérive, aucune structure
    prices = 100.0 * np.exp(np.cumsum(log_steps))
    idx = pd.date_range("2020-01-01", periods=N_BARS, freq="1h", tz="UTC")
    o = pd.Series(prices, index=idx)
    c = o.shift(-1).fillna(o)
    return pd.DataFrame(
        {"open": o, "high": np.maximum(o, c), "low": np.minimum(o, c), "close": c, "volume": 1.0}
    )


def ema_cross_targets(df: pd.DataFrame) -> pd.DataFrame:
    """Stratégie témoin honnête : EMA(10) > EMA(30) sur le close -> long."""
    fast = df["close"].ewm(span=10, adjust=False).mean()
    slow = df["close"].ewm(span=30, adjust=False).mean()
    return pd.DataFrame({"X": (fast > slow).astype(float)}, index=df.index)


def cheating_targets(df: pd.DataFrame) -> pd.DataFrame:
    """CANARI : regarde le rendement FUTUR open[t+1]->open[t+2] (lookahead volontaire)."""
    future_ret = df["open"].shift(-2) / df["open"].shift(-1) - 1.0
    return pd.DataFrame({"X": (future_ret > 0).astype(float)}, index=df.index)


def run_seeds(strategy, cost: CostModel) -> np.ndarray:
    logs = []
    for seed in range(N_SEEDS):
        df = random_walk_ohlcv(seed)
        res = run_backtest({"X": df}, strategy(df), cost)
        logs.append(math.log(float(res.equity.iloc[-1])))
    return np.array(logs)


def test_honest_strategy_earns_nothing_on_noise_before_costs() -> None:
    logs = run_seeds(ema_cross_targets, CostModel(0.0, 0.0))
    # Borne : ~3 erreurs types de la moyenne (exposition ~50 %).
    se = SIGMA * math.sqrt(N_BARS) * 0.75 / math.sqrt(N_SEEDS)
    assert abs(logs.mean()) < 3 * se, (
        f"Une stratégie honnête 'gagne' {logs.mean():+.3f} (log) sur du bruit pur "
        f"-> suspicion de lookahead dans le moteur"
    )


def test_honest_strategy_loses_after_costs_on_noise() -> None:
    gross = run_seeds(ema_cross_targets, CostModel(0.0, 0.0))
    net = run_seeds(ema_cross_targets, CostModel(0.001, 0.0005))
    assert net.mean() < gross.mean(), "les coûts doivent dégrader la performance"
    assert net.mean() < 0, (
        f"après frais, l'espérance sur bruit pur doit être négative (obtenu {net.mean():+.3f})"
    )


def test_canary_cheating_strategy_is_caught() -> None:
    """Le test précédent doit être capable de détecter un vrai lookahead."""
    logs = run_seeds(cheating_targets, CostModel(0.0, 0.0))
    se = SIGMA * math.sqrt(N_BARS) * 0.75 / math.sqrt(N_SEEDS)
    # Le tricheur explose la borne : preuve que la borne détecte le lookahead.
    assert logs.mean() > 3 * se, (
        "le canari tricheur aurait dû être détecté — le test random-walk n'a plus de mordant"
    )
