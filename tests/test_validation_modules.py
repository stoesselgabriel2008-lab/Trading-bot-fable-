"""Tests unitaires des modules de validation (Phase 6)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.validation.dsr import (
    deflated_sharpe_ratio,
    expected_max_sharpe,
    probabilistic_sharpe_ratio,
    sharpe_non_annualized,
)
from src.validation.montecarlo import bootstrap_trades
from src.validation.regimes import classify_regimes, returns_by_regime
from src.validation.splits import split_data, split_frame


def series(values, freq="1D") -> pd.Series:
    idx = pd.date_range("2020-01-01", periods=len(values), freq=freq, tz="UTC")
    return pd.Series(values, index=idx, dtype=float)


# ------------------------------------------------------------------ splits
def test_split_frame_proportions_and_order() -> None:
    df = pd.DataFrame({"x": range(1000)}, index=pd.date_range("2020-01-01", periods=1000, tz="UTC"))
    s = split_frame(df)
    assert len(s.dev) == 700 and len(s.validation) == 150 and len(s.test_final) == 150
    # aucun chevauchement, ordre chronologique strict
    assert s.dev.index[-1] < s.validation.index[0] < s.test_final.index[0]


def test_split_data_common_calendar_dates() -> None:
    long = pd.DataFrame(
        {"close": range(1000)}, index=pd.date_range("2020-01-01", periods=1000, tz="UTC")
    )
    short = long.iloc[600:].copy()  # actif listé plus tard
    dev, val, test = split_data({"L": long, "S": short})
    # les bornes calendaires sont les mêmes pour les deux actifs
    assert dev["L"].index[-1] == dev["S"].index[-1] if len(dev["S"]) else True
    assert len(dev["L"]) == 700
    assert len(val["L"]) == 150 and len(test["L"]) == 150


# ------------------------------------------------------------------ DSR
def test_sharpe_non_annualized_known_value() -> None:
    r = series([0.01, -0.01] * 50)
    assert sharpe_non_annualized(r) == pytest.approx(0.0, abs=1e-9)


def test_psr_high_for_strong_consistent_returns() -> None:
    rng = np.random.default_rng(1)
    good = series(rng.normal(0.002, 0.01, 500))  # SR/bougie = 0.2
    assert probabilistic_sharpe_ratio(good, 0.0) > 0.99


def test_expected_max_sharpe_grows_with_trials() -> None:
    v = 0.01
    assert expected_max_sharpe(100, v) > expected_max_sharpe(10, v) > 0
    assert expected_max_sharpe(1, v) == 0.0


def test_dsr_penalizes_many_trials() -> None:
    rng = np.random.default_rng(2)
    rets = series(rng.normal(0.0008, 0.01, 400))
    few = deflated_sharpe_ratio(rets, n_trials=2)
    many = deflated_sharpe_ratio(rets, n_trials=500)
    assert many["dsr"] < few["dsr"]  # plus d'essais -> moins de confiance
    assert 0.0 <= many["p_random"] <= 1.0


# ------------------------------------------------------------------ Monte Carlo
def test_bootstrap_requires_min_trades() -> None:
    assert bootstrap_trades([0.01] * 5) is None


def test_bootstrap_statistics_sane() -> None:
    rng = np.random.default_rng(3)
    pnls = list(rng.normal(0.01, 0.05, 200))
    mc = bootstrap_trades(pnls, n_draws=1000)
    assert mc is not None
    assert mc.ret_ci_low < mc.ret_mean < mc.ret_ci_high
    assert mc.dd_p95 <= mc.dd_median <= 0
    assert 0.0 <= mc.prob_negative <= 1.0


def test_bootstrap_all_losses_probability_one() -> None:
    mc = bootstrap_trades([-0.01] * 50)
    assert mc is not None
    assert mc.prob_negative == 1.0


# ------------------------------------------------------------------ régimes
def test_classify_regimes_bull_bear() -> None:
    up = series(np.linspace(100, 400, 400))
    reg_up = classify_regimes(up)
    assert (reg_up.iloc[250:] == "bull").mean() > 0.9

    crash = series(list(np.linspace(100, 200, 300)) + list(np.linspace(200, 80, 100)))
    reg_crash = classify_regimes(crash)
    assert (reg_crash.iloc[-30:] == "bear").all()


def test_returns_by_regime_partitions_everything() -> None:
    close = series(list(np.linspace(100, 200, 300)) + list(np.linspace(200, 80, 100)))
    regimes = classify_regimes(close)
    rets = close.pct_change().fillna(0.0)
    table = returns_by_regime(rets, regimes)
    assert int(table["n_bars"].sum()) == len(rets)
    assert set(table.index) == {"bull", "bear", "range"}
