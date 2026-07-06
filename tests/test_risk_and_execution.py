"""Tests du risk manager, des circuit breakers, de la persistance et du broker paper."""

from __future__ import annotations

import pytest

from src.execution.broker import PaperBroker
from src.execution.state import Position, StateStore, new_client_order_id, reconcile
from src.risk.breakers import Action, CircuitBreakers
from src.risk.manager import RiskManager
from src.utils.config import load_risk_config


@pytest.fixture
def risk_cfg():
    return load_risk_config()


# ------------------------------------------------------------------ RiskManager (R8)
def test_clamp_position_and_exposure(risk_cfg) -> None:
    rm = RiskManager(risk_cfg)
    # Demande volontairement au-delà de toutes les limites.
    targets = {"BTC/USDT": 0.9, "ETH/USDT": 0.5, "SOL/USDT": 0.4}
    out, report = rm.clamp_targets(targets)
    assert report.was_clamped
    limits = risk_cfg.limits
    assert all(w <= limits.max_position_pct + 1e-9 for w in out.values())
    assert sum(out.values()) <= limits.max_total_exposure_pct + 1e-9


def test_clamp_respects_reasonable_request(risk_cfg) -> None:
    rm = RiskManager(risk_cfg)
    targets = {"BTC/USDT": 0.10, "ETH/USDT": 0.10}
    out, report = rm.clamp_targets(targets)
    assert out == targets
    assert not report.was_clamped


def test_order_size_capped(risk_cfg) -> None:
    rm = RiskManager(risk_cfg)
    clamped, refusal = rm.clamp_order_size("BTC/USDT", 0.5)
    assert clamped == risk_cfg.limits.max_order_pct
    assert refusal is not None
    ok, none_ = rm.clamp_order_size("BTC/USDT", 0.05)
    assert ok == 0.05 and none_ is None


def test_leverage_forbidden_by_default(risk_cfg) -> None:
    assert RiskManager(risk_cfg).leverage_forbidden()


# ------------------------------------------------------------------ Circuit breakers (R9)
def make_breakers(risk_cfg, t0=1_000_000.0):
    clock = {"t": t0}
    cb = CircuitBreakers(risk_cfg, clock=lambda: clock["t"])
    return cb, clock


def test_consecutive_losses_trigger_pause(risk_cfg) -> None:
    cb, clock = make_breakers(risk_cfg)
    assert cb.check(10_000).action is Action.CONTINUE
    for _ in range(risk_cfg.circuit_breakers.max_consecutive_losses):
        cb.record_trade_result(-10.0)
    assert cb.check(10_000).action is Action.PAUSE
    # La pause expire.
    clock["t"] += risk_cfg.circuit_breakers.pause_after_losses_minutes * 60 + 1
    assert cb.check(10_000).action is Action.CONTINUE


def test_daily_loss_halts(risk_cfg) -> None:
    cb, clock = make_breakers(risk_cfg)
    cb.check(10_000)  # initialise la journée
    clock["t"] += 60
    loss = risk_cfg.limits.max_daily_loss_pct + 0.01
    status = cb.check(10_000 * (1 - loss))
    assert status.action is Action.HALT
    assert "journalière" in status.reason


def test_drawdown_halts(risk_cfg) -> None:
    cb, clock = make_breakers(risk_cfg)
    cb.check(10_000)
    # on avance les fenêtres horaires/journalières pour isoler le drawdown
    clock["t"] += 90_000
    cb.check(10_000)
    clock["t"] += 90_000
    dd = risk_cfg.limits.max_drawdown_pct + 0.02
    status = cb.check(10_000 * (1 - dd))
    assert status.action is Action.HALT
    assert "drawdown" in status.reason


def test_api_error_rate_halts(risk_cfg) -> None:
    cb, _ = make_breakers(risk_cfg)
    for _ in range(risk_cfg.circuit_breakers.max_api_errors_per_hour + 1):
        cb.record_api_error()
    assert cb.check(10_000).action is Action.HALT


def test_reconciliation_divergence_halts(risk_cfg) -> None:
    cb, _ = make_breakers(risk_cfg)
    status = cb.record_reconciliation_divergence(local=1.0, remote=1.5)
    assert status.action is Action.HALT
    ok = cb.record_reconciliation_divergence(local=1.0, remote=1.0000001)
    assert ok.action is Action.CONTINUE


# ------------------------------------------------------------------ StateStore
def test_state_roundtrip_positions_orders_decisions(tmp_path) -> None:
    store = StateStore(tmp_path / "bot.sqlite")
    store.upsert_position(Position("BTC/USDT", 0.5, 50_000))
    assert store.get_positions()["BTC/USDT"].qty == 0.5

    coid = new_client_order_id()
    store.record_order(coid, "BTC/USDT", "buy", 0.5, 50_000)
    assert store.order_exists(coid)
    assert coid in store.pending_orders()
    store.update_order_status(coid, "filled")
    assert coid not in store.pending_orders()
    # Idempotence : ré-enregistrer le même clientOrderId est sans effet.
    store.record_order(coid, "BTC/USDT", "buy", 99.0, 1.0)
    assert store.get_positions()["BTC/USDT"].qty == 0.5

    store.log_decision("no_trade", None, {"reason": "test"})
    kinds = [d[1] for d in store.decisions()]
    assert "no_trade" in kinds
    store.close()


def test_reconcile_detects_divergence() -> None:
    local = {"BTC/USDT": Position("BTC/USDT", 1.0, 100)}
    assert reconcile(local, {"BTC/USDT": 1.0}, 0.01) == []
    problems = reconcile(local, {"BTC/USDT": 1.2}, 0.01)
    assert problems and "BTC/USDT" in problems[0]
    assert reconcile(local, {}, 0.01)  # position locale absente de l'exchange


# ------------------------------------------------------------------ PaperBroker
def test_paper_broker_buy_sell_with_fees_and_slippage() -> None:
    b = PaperBroker(initial_cash=10_000, taker_fee=0.001, slippage_bps=10)
    fill = b.market_order("BTC/USDT", "buy", qty=0.1, ref_price=50_000)
    assert fill.price == pytest.approx(50_000 * 1.001)  # slippage 10 bps
    assert b.positions["BTC/USDT"] == pytest.approx(0.1)
    expected_cash = 10_000 - 0.1 * 50_050 * 1.001
    assert b.cash == pytest.approx(expected_cash)

    b.market_order("BTC/USDT", "sell", qty=0.1, ref_price=50_000)
    assert b.positions["BTC/USDT"] == pytest.approx(0.0)
    # Aller-retour au même prix : on perd frais + slippage, jamais plus.
    assert 9_960 < b.cash < 10_000


def test_paper_broker_rejects_overdraft_and_short() -> None:
    b = PaperBroker(initial_cash=100, taker_fee=0.001, slippage_bps=0)
    with pytest.raises(ValueError):
        b.market_order("BTC/USDT", "buy", qty=1.0, ref_price=50_000)
    with pytest.raises(ValueError):
        b.market_order("BTC/USDT", "sell", qty=0.1, ref_price=50_000)
