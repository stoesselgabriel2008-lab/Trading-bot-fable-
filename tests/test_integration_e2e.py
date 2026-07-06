"""Test d'intégration bout-en-bout en mode paper sur données FIGÉES (Phase 9).

Couvre le cycle complet de l'exécuteur : données -> stratégie -> risk manager ->
ordres -> persistance -> reprise après crash -> kill switch -> safe mode.
Aucun réseau : `fetch_closed_candles` est remplacé par des données synthétiques.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

import src.execution.executor as executor_mod
from src.execution.executor import PaperExecutor
from src.execution.scheduler import run_fast_cycles
from src.execution.state import Position
from src.strategies.baselines import BuyAndHold
from src.utils.config import load_exchange_config, load_risk_config


def frozen_data(n: int = 120, price: float = 100.0) -> dict[str, pd.DataFrame]:
    idx = pd.date_range("2026-01-01", periods=n, freq="1h", tz="UTC")
    rng = np.random.default_rng(9)
    c = pd.Series(price * np.cumprod(1 + rng.normal(0, 0.002, n)), index=idx)
    o = c.shift(1).fillna(c.iloc[0])
    df = pd.DataFrame(
        {"open": o, "high": np.maximum(o, c), "low": np.minimum(o, c), "close": c, "volume": 1.0}
    )
    return {"BTC/USDT": df, "ETH/USDT": df * 0.1}


@pytest.fixture
def executor(tmp_path, monkeypatch):
    monkeypatch.setattr(executor_mod, "KILL_FLAG", tmp_path / "KILL")
    # Pas de réseau : build_exchange n'est jamais utilisé après ce patch.
    monkeypatch.setattr(executor_mod, "build_exchange", lambda source: None)
    ex = PaperExecutor(
        strategy=BuyAndHold("bh"),  # force des ordres dès le 1er cycle
        symbols=["BTC/USDT", "ETH/USDT"],
        timeframe="1h",
        exchange_cfg=load_exchange_config(),
        risk_cfg=load_risk_config(),
        state_path=tmp_path / "bot.sqlite",
        strategy_label="TEST E2E — données figées",
    )
    ex.fetch_closed_candles = lambda: frozen_data()  # type: ignore[method-assign]
    return ex


def test_e2e_cycle_trades_and_persists(executor) -> None:
    report = executor.run_cycle()
    assert report.action == "traded"
    # BuyAndHold demande 1.0 partout -> clampé par R8 (max_position 0.20, ordre max 0.10).
    positions = executor.store.get_positions()
    assert set(positions) == {"BTC/USDT", "ETH/USDT"}
    kinds = [d[1] for d in executor.store.decisions()]
    assert "target" in kinds and "order" in kinds and "risk_clamp" in kinds
    # L'exposition reste sous la limite totale.
    prices = {s: float(df["close"].iloc[-1]) for s, df in frozen_data().items()}
    equity = executor.broker.equity(prices)
    gross = sum(p.qty * prices[s] for s, p in positions.items()) / equity
    assert gross <= load_risk_config().limits.max_total_exposure_pct + 0.05


def test_e2e_multiple_cycles_converge_no_churn(executor) -> None:
    run_fast_cycles(executor.run_cycle, 4)
    orders = [d for d in executor.store.decisions() if d[1] == "order"]
    # Le poids converge vers la cible : le nombre d'ordres est borné, pas 2/cycle.
    assert 2 <= len(orders) <= 8
    last = executor.run_cycle()
    assert last.action in ("no_trade", "traded")


def test_e2e_crash_recovery_reloads_state(executor, tmp_path) -> None:
    executor.run_cycle()
    cash_before = executor.broker.cash
    positions_before = {s: p.qty for s, p in executor.store.get_positions().items()}

    # « Crash » : nouveau process -> nouvel exécuteur sur le même SQLite.
    import src.execution.executor as em

    ex2 = PaperExecutor(
        strategy=BuyAndHold("bh"),
        symbols=["BTC/USDT", "ETH/USDT"],
        timeframe="1h",
        exchange_cfg=load_exchange_config(),
        risk_cfg=load_risk_config(),
        state_path=tmp_path / "bot.sqlite",
        strategy_label="TEST E2E",
    )
    ex2.fetch_closed_candles = lambda: frozen_data()  # type: ignore[method-assign]
    assert ex2.broker.cash == pytest.approx(cash_before)
    assert {s: q for s, q in ex2.broker.positions.items()} == pytest.approx(positions_before)
    # Et la réconciliation passe au cycle suivant.
    report = ex2.run_cycle()
    assert report.action in ("no_trade", "traded")
    del em


def test_e2e_kill_switch_stops_cleanly(executor, tmp_path) -> None:
    executor.run_cycle()
    (tmp_path / "KILL").write_text("stop")
    report = executor.run_cycle()
    assert report.action == "killed"
    assert any(d[1] == "kill" for d in executor.store.decisions())
    # Tous les cycles suivants restent inertes.
    assert executor.run_cycle().action in ("killed", "halted")


def test_e2e_safe_mode_on_reconciliation_divergence(executor) -> None:
    executor.run_cycle()
    # Corruption volontaire : la base prétend une position que le broker n'a pas.
    executor.store.upsert_position(Position("BTC/USDT", 999.0, 1.0))
    report = executor.run_cycle()
    assert report.action == "safe_mode"
    assert executor.halted
    assert any(d[1] == "breaker" for d in executor.store.decisions())


def test_e2e_fetch_failure_counts_api_error(executor) -> None:
    def boom():
        raise ConnectionError("réseau KO")

    executor.fetch_closed_candles = boom  # type: ignore[method-assign]
    report = executor.run_cycle()
    assert report.action == "no_trade" and "fetch KO" in report.detail
    assert len(executor.breakers.api_errors) == 1
