"""Tests des stratégies (Phase 5) : séries construites à la main + causalité générique."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.strategies.baselines import BuyAndHold, RandomTiming
from src.strategies.families import (
    FAMILIES,
    AtrBreakout,
    ConditionalDca,
    CrossSectionalMomentum,
    DonchianBreakout,
    EmaCross,
    GridRange,
    MeanReversion,
    VolTargetOverlay,
)


def ohlcv(closes: np.ndarray | list[float], start: str = "2024-01-01") -> pd.DataFrame:
    c = pd.Series(np.asarray(closes, dtype=float))
    idx = pd.date_range(start, periods=len(c), freq="1D", tz="UTC")
    c.index = idx
    o = c.shift(1).fillna(c.iloc[0])
    return pd.DataFrame(
        {
            "open": o,
            "high": np.maximum(o, c) * 1.001,
            "low": np.minimum(o, c) * 0.999,
            "close": c,
            "volume": 1.0,
        }
    )


# ------------------------------------------------------------- cas manuels
def test_ema_cross_long_in_uptrend_flat_in_downtrend() -> None:
    up = ohlcv(np.linspace(100, 200, 120))
    down = ohlcv(np.linspace(200, 100, 120))
    strat = EmaCross("s", {"fast": 10, "slow": 30, "trend_filter": 0})
    t_up = strat.generate_targets({"X": up})["X"]
    t_down = strat.generate_targets({"X": down})["X"]
    assert t_up.iloc[-1] == 1.0 and t_up.iloc[60:].mean() > 0.9
    assert t_down.iloc[-1] == 0.0 and t_down.iloc[60:].mean() < 0.1


def test_donchian_enters_on_breakout_exits_on_breakdown() -> None:
    closes = [100.0] * 30 + [120.0] * 10 + [80.0] * 10  # breakout puis effondrement
    strat = DonchianBreakout("s", {"entry": 20, "exit": 10})
    t = strat.generate_targets({"X": ohlcv(closes)})["X"]
    assert t.iloc[29] == 0.0  # avant breakout : flat
    assert t.iloc[31] == 1.0  # après cassure du plus haut 20 jours : long
    assert t.iloc[-1] == 0.0  # après cassure du plus bas 10 jours : sorti


def test_mean_reversion_enters_on_crash_exits_on_recovery() -> None:
    closes = [100.0] * 30 + [70.0] + [100.0] * 10  # crash -30 % puis récupération
    strat = MeanReversion(
        "s", {"rsi_period": 14, "rsi_entry": 35, "z_window": 20, "z_entry": -1.5, "time_stop": 10}
    )
    t = strat.generate_targets({"X": ohlcv(closes)})["X"]
    assert t.iloc[30] == 1.0  # entrée le jour du crash
    assert t.iloc[-1] == 0.0  # RSI > 50 après récupération : sorti
    assert t.iloc[:29].sum() == 0.0  # jamais long avant


def test_mean_reversion_time_stop_cuts_position() -> None:
    closes = [100.0] * 30 + [70.0] * 20  # crash SANS récupération
    strat = MeanReversion(
        "s", {"rsi_period": 14, "rsi_entry": 35, "z_window": 20, "z_entry": -1.5, "time_stop": 5}
    )
    t = strat.generate_targets({"X": ohlcv(closes)})["X"]
    assert t.iloc[30] == 1.0
    assert t.iloc[40] == 0.0  # coupé par le time-stop bien avant la fin


def test_atr_breakout_enters_and_trails_out() -> None:
    closes = [100.0] * 30 + list(np.linspace(101, 130, 10)) + [90.0] * 5
    strat = AtrBreakout("s", {"lookback": 20, "k_entry": 0.5, "k_exit": 2.0})
    t = strat.generate_targets({"X": ohlcv(closes)})["X"]
    assert t.iloc[:30].sum() == 0.0
    assert t.iloc[35] == 1.0  # long pendant la montée
    assert t.iloc[-1] == 0.0  # trailing stop touché après la chute


def test_momentum_xs_selects_winner_only_if_positive() -> None:
    up = ohlcv(np.linspace(100, 200, 120))
    down = ohlcv(np.linspace(200, 100, 120))
    strat = CrossSectionalMomentum("s", {"lookback": 30, "top_k": 1, "rebalance_every": 1})
    t = strat.generate_targets({"UP": up, "DOWN": down})
    assert t["UP"].iloc[-1] == 1.0
    assert t["DOWN"].iloc[-1] == 0.0
    # Les deux en baisse -> filtre absolu : aucune position.
    t2 = strat.generate_targets({"A": down, "B": ohlcv(np.linspace(150, 90, 120))})
    assert t2.iloc[-1].sum() == 0.0


def test_conditional_dca_scales_with_discount() -> None:
    strat = ConditionalDca("s", {"ma_window": 10, "max_discount": 0.3})
    flat = ohlcv([100.0] * 40)
    t = strat.generate_targets({"X": flat})["X"]
    assert t.iloc[-1] == pytest.approx(0.5, abs=0.01)  # au prix moyen : 50 %
    crash = ohlcv([100.0] * 39 + [70.0])  # -30 % sous la SMA -> plein
    t2 = strat.generate_targets({"X": crash})["X"]
    assert t2.iloc[-1] > 0.9
    pump = ohlcv([100.0] * 39 + [140.0])  # +40 % au-dessus -> 0
    t3 = strat.generate_targets({"X": pump})["X"]
    assert t3.iloc[-1] == 0.0


def test_grid_range_full_at_bottom_stopped_below() -> None:
    strat = GridRange("s", {"ma_window": 10, "range_pct": 0.10})
    at_center = ohlcv([100.0] * 40)
    assert strat.generate_targets({"X": at_center})["X"].iloc[-1] == pytest.approx(0.5, abs=0.02)
    near_bottom = ohlcv([100.0] * 39 + [91.0])  # -9 % : bas de grille
    w = strat.generate_targets({"X": near_bottom})["X"].iloc[-1]
    assert 0.8 < w <= 1.0
    below_range = ohlcv([100.0] * 39 + [85.0])  # -15 % : STOP global
    assert strat.generate_targets({"X": below_range})["X"].iloc[-1] == 0.0


def test_vol_target_overlay_scales_down_high_vol() -> None:
    rng = np.random.default_rng(3)
    calm = ohlcv(100 * np.cumprod(1 + rng.normal(0.001, 0.005, 200)))
    wild = ohlcv(100 * np.cumprod(1 + rng.normal(0.001, 0.08, 200)))
    inner = BuyAndHold("bh")
    strat = VolTargetOverlay("s", {"target_vol_annual": 0.40, "vol_window": 30}, inner=inner)
    w_calm = strat.generate_targets({"X": calm})["X"].iloc[-1]
    w_wild = strat.generate_targets({"X": wild})["X"].iloc[-1]
    assert w_calm == 1.0  # vol faible : plafonné à 1, jamais de levier
    assert w_wild < 0.5  # vol énorme : exposition fortement réduite


def test_buy_and_hold_always_one() -> None:
    t = BuyAndHold("bh").generate_targets({"X": ohlcv([100.0] * 20)})
    assert (t["X"] == 1.0).all()


def test_random_timing_reproducible_and_calibrated() -> None:
    df = ohlcv(list(100 + np.arange(3000, dtype=float)))
    s1 = RandomTiming("r", {"hold_bars": 20, "seed": 42})
    s2 = RandomTiming("r", {"hold_bars": 20, "seed": 42})
    t1, t2 = s1.generate_targets({"X": df}), s2.generate_targets({"X": df})
    pd.testing.assert_frame_equal(t1, t2)  # reproductible
    exposure = t1["X"].mean()
    assert 0.35 < exposure < 0.65  # ~50 % attendu


# ------------------------------------------------- tests génériques (toutes familles)
def _instances() -> list:
    out = []
    for name, cls in FAMILIES.items():
        if cls is VolTargetOverlay:
            out.append(cls("vt", cls.presets["balanced"], inner=BuyAndHold("bh")))
        else:
            out.append(cls.from_preset(name, "balanced"))
    out.append(BuyAndHold("bh"))
    out.append(RandomTiming("rt", {"hold_bars": 10, "seed": 1}))
    return out


@pytest.mark.parametrize("strat", _instances(), ids=lambda s: s.name)
def test_targets_bounded_and_nan_free(strat) -> None:
    rng = np.random.default_rng(11)
    data = {
        "A": ohlcv(100 * np.cumprod(1 + rng.normal(0.001, 0.03, 400))),
        "B": ohlcv(100 * np.cumprod(1 + rng.normal(0.0, 0.04, 400))),
    }
    t = strat.generate_targets(data)
    assert not t.isna().any().any()
    assert float(t.min().min()) >= 0.0
    assert float(t.max().max()) <= 1.0
    assert set(t.columns) == {"A", "B"}


@pytest.mark.parametrize("strat", _instances(), ids=lambda s: s.name)
def test_causality_future_change_does_not_alter_past_targets(strat) -> None:
    """Contrat anti-lookahead de l'interface : réécrire le futur ne change pas
    les poids passés (les 60 premières % de la série restent identiques)."""
    rng = np.random.default_rng(23)
    base = {
        "A": ohlcv(100 * np.cumprod(1 + rng.normal(0.001, 0.03, 500))),
        "B": ohlcv(100 * np.cumprod(1 + rng.normal(0.0, 0.04, 500))),
    }
    tampered = {sym: df.copy() for sym, df in base.items()}
    for df in tampered.values():
        df.iloc[300:, :4] *= 3.0  # réécriture massive du futur (O/H/L/C)

    t_base = strat.generate_targets(base)
    t_tamp = strat.generate_targets(tampered)
    pd.testing.assert_frame_equal(t_base.iloc[:299], t_tamp.iloc[:299], check_freq=False)
