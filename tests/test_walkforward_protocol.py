"""Tests du walk-forward, de la sensibilité et du protocole complet (synthétique rapide)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.backtest.engine import CostModel
from src.strategies.families import EmaCross
from src.utils.config import load_exchange_config
from src.validation.protocol import validate_couple
from src.validation.sensitivity import sensitivity_analysis
from src.validation.walkforward import grid_from_presets, walk_forward


def synth_data(n: int = 900, drift: float = 0.001, seed: int = 4) -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    c = pd.Series(
        100 * np.cumprod(1 + rng.normal(drift, 0.02, n)),
        index=pd.date_range("2019-01-01", periods=n, freq="1D", tz="UTC"),
    )
    o = c.shift(1).fillna(c.iloc[0])
    return {
        "X": pd.DataFrame(
            {
                "open": o,
                "high": np.maximum(o, c) * 1.001,
                "low": np.minimum(o, c) * 0.999,
                "close": c,
                "volume": 1.0,
            }
        )
    }


def test_grid_from_presets_contains_presets_and_variants() -> None:
    grid = grid_from_presets(EmaCross)
    assert EmaCross.presets["balanced"] in grid
    assert len(grid) >= 3
    # aucun doublon
    assert all(grid.count(g) == 1 for g in grid)


def test_walk_forward_produces_oos_windows() -> None:
    data = synth_data()
    wf = walk_forward(EmaCross, data, CostModel(0.001, 0.0005), "1d", is_bars=300, oos_bars=100)
    assert len(wf.windows) >= 4
    assert wf.n_configs_tested == len(grid_from_presets(EmaCross)) * len(wf.windows)
    assert len(wf.oos_returns) > 300
    assert wf.oos_metrics is not None
    assert 0.0 <= wf.pct_windows_positive <= 1.0
    # Les fenêtres OOS sont chronologiques et disjointes.
    starts = [w.oos_start for w in wf.windows]
    assert starts == sorted(starts)


def test_sensitivity_reports_neighbors() -> None:
    data = synth_data()
    res = sensitivity_analysis(
        EmaCross, dict(EmaCross.presets["balanced"]), data, CostModel(0.001, 0.0005), "1d"
    )
    assert not res.grid.empty
    assert {"param", "factor", "value", "sharpe"} <= set(res.grid.columns)
    assert isinstance(res.is_robust, bool)


@pytest.mark.slow
def test_protocol_full_run_returns_verdict() -> None:
    cfg = load_exchange_config()
    data = synth_data(n=1400)
    v = validate_couple(EmaCross, "SYNTH", data, cfg.fees, cfg.slippage, "1d", 500, 150)
    assert v.verdict in ("VALIDÉE", "REJETÉE")
    assert v.n_configs_tested > 0
    assert set(v.criteria) == {
        "C1_rendement_net_positif_stress",
        "C2_sharpe_oos_min_0.8",
        "C3_max_dd_max_30pct",
        "C4_profit_factor_min_1.15",
        "C5_min_60pct_fenetres_positives",
        "C6_bat_baseline_aleatoire_p90",
        "C7_calmar_competitif_vs_bh",
        "C8_robustesse_parametres",
    }
    assert 0.0 <= v.dsr["p_random"] <= 1.0
    assert v.regime_table is not None
    # Test final rempli UNIQUEMENT si validée.
    assert (v.final_test_return is not None) == (v.verdict == "VALIDÉE")


def test_protocol_insufficient_history_rejected() -> None:
    cfg = load_exchange_config()
    data = synth_data(n=200)  # bien trop court pour IS 500
    v = validate_couple(EmaCross, "SHORT", data, cfg.fees, cfg.slippage, "1d", 500, 150)
    assert v.verdict == "REJETÉE"
    assert "insuffisant" in v.reasons[0]
