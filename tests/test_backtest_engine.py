"""Tests du moteur de backtest (Phase 4) : cas manuel + timing d'exécution."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.backtest.engine import CostModel, run_backtest
from src.backtest.metrics import compute_metrics


def ohlcv_from_opens(opens: list[float]) -> pd.DataFrame:
    idx = pd.date_range("2024-01-01", periods=len(opens), freq="1D", tz="UTC")
    o = pd.Series(opens, index=idx, dtype=float)
    c = o.shift(-1).fillna(o)  # close[t] = open[t+1] (continuité parfaite)
    return pd.DataFrame(
        {"open": o, "high": np.maximum(o, c), "low": np.minimum(o, c), "close": c, "volume": 1.0}
    )


def weights_frame(index: pd.DatetimeIndex, values: list[float], column: str = "X") -> pd.DataFrame:
    return pd.DataFrame({column: values}, index=index, dtype=float)


# ------------------------------------------------------------------
# 1. Mini-cas de 10 bougies vérifié À LA MAIN (critère d'acceptation)
# ------------------------------------------------------------------
def test_hand_verified_ten_candles() -> None:
    opens = [100, 102, 101, 105, 110, 108, 112, 115, 113, 120]
    df = ohlcv_from_opens(opens)
    # Poids cibles décidés à la clôture de t :
    targets = weights_frame(df.index, [0, 1, 1, 0, 0, 0.5, 0.5, 0, 0, 0])
    cost = CostModel(fee_rate=0.01, slippage_rate=0.0)
    res = run_backtest({"X": df}, targets, cost)

    # Poids effectifs = cibles décalées d'une bougie (exécution à l'open t+1).
    assert res.effective_weights["X"].tolist() == [0, 0, 1, 1, 0, 0, 0.5, 0.5, 0, 0]

    # Calcul manuel :
    # t2 : coût 1%, rendement 105/101 ; t3 : rendement 110/105 ; t4 : coût 1%
    # t6 : coût 0.5%, rendement 0.5*(115/112-1) ; t7 : 0.5*(113/115-1) ; t8 : coût 0.5%
    expected = (
        0.99
        * (105 / 101)
        * (110 / 105)
        * 0.99
        * 0.995
        * (1 + 0.5 * (115 / 112 - 1))
        * (1 + 0.5 * (113 / 115 - 1))
        * 0.995
    )
    assert res.equity.iloc[-1] == pytest.approx(expected, rel=1e-12)

    # 2 épisodes de trade (t2-t3 et t6-t7), turnover total = 1+1+0.5+0.5 = 3.
    assert len(res.trades) == 2
    assert [t.bars_held for t in res.trades] == [2, 2]
    assert res.turnover.sum() == pytest.approx(3.0)

    m = compute_metrics(res, "1d")
    assert m.n_trades == 2
    assert m.total_costs_frac == pytest.approx(0.01 + 0.01 + 0.005 + 0.005)
    assert m.avg_exposure == pytest.approx(3.0 / 10.0)


# ------------------------------------------------------------------
# 2. Timing d'exécution : un signal en t ne capte JAMAIS le mouvement de t
# ------------------------------------------------------------------
def test_signal_at_t_captures_only_next_period() -> None:
    # Saut de prix massif entre open[5] et open[6] : +50 %.
    opens = [100.0] * 5 + [150.0, 150.0, 150.0]
    df = ohlcv_from_opens(opens)
    cost = CostModel(0.0, 0.0)

    # Signal posé en t=4 (dernier moment où le saut serait captable SANS lookahead
    # est interdit : poids effectif à l'open de 5, rendement open5->open6 = 0 %... )
    targets = weights_frame(df.index, [0, 0, 0, 0, 1, 0, 0, 0])
    res = run_backtest({"X": df}, targets, cost)
    # Effectif à open[5]=150 -> open[6]=150 : aucun gain.
    assert res.equity.iloc[-1] == pytest.approx(1.0)

    # Signal posé en t=3 : effectif à open[4]=100 -> open[5]=150 : +50 %.
    targets2 = weights_frame(df.index, [0, 0, 0, 1, 0, 0, 0, 0])
    res2 = run_backtest({"X": df}, targets2, cost)
    assert res2.equity.iloc[-1] == pytest.approx(1.5)


def test_future_data_change_does_not_affect_past_equity() -> None:
    rng = np.random.default_rng(7)
    opens = list(100 * np.cumprod(1 + rng.normal(0, 0.01, 50)))
    df = ohlcv_from_opens(opens)
    targets = weights_frame(df.index, list((np.arange(50) % 3 == 0).astype(float)))
    cost = CostModel(0.001, 0.0005)

    base = run_backtest({"X": df}, targets, cost)

    tampered = df.copy()
    tampered.iloc[30:, tampered.columns.get_loc("open")] *= 2.0  # on réécrit le futur
    res = run_backtest({"X": tampered}, targets, cost)

    # L'equity jusqu'à t=29 inclus est STRICTEMENT identique.
    pd.testing.assert_series_equal(base.equity.iloc[:29], res.equity.iloc[:29], check_freq=False)


# ------------------------------------------------------------------
# Garde-fous divers
# ------------------------------------------------------------------
def test_no_leverage_gross_exposure_capped() -> None:
    df = ohlcv_from_opens([100.0] * 6)
    idx = df.index
    targets = pd.DataFrame({"A": [0.8] * 6, "B": [0.8] * 6}, index=idx)  # brut = 1.6
    res = run_backtest({"A": df, "B": df.copy()}, targets, CostModel(0.0, 0.0))
    gross = res.effective_weights.sum(axis=1)
    assert gross.max() <= 1.0 + 1e-12


def test_missing_asset_bars_get_zero_weight() -> None:
    df_a = ohlcv_from_opens([100.0] * 10)
    df_b = ohlcv_from_opens([100.0] * 10).iloc[5:]  # B listé plus tard
    targets = pd.DataFrame({"A": [0.5] * 10, "B": [0.5] * 10}, index=df_a.index)
    res = run_backtest({"A": df_a, "B": df_b}, targets, CostModel(0.0, 0.0))
    assert (res.effective_weights["B"].iloc[:5] == 0).all()
