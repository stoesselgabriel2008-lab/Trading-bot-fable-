"""Tests du chargement de configuration (Phase 0)."""

import pytest
from pydantic import ValidationError

from src.utils.config import (
    RiskConfig,
    load_assets_config,
    load_exchange_config,
    load_risk_config,
    load_strategies_config,
)


def test_assets_config_loads() -> None:
    cfg = load_assets_config()
    symbols = [a.symbol for a in cfg.assets]
    assert "BTC/USDT" in symbols
    assert set(cfg.timeframes) >= {"1h", "4h", "1d"}


def test_risk_config_loads_and_is_sane() -> None:
    cfg = load_risk_config()
    assert cfg.capital.initial > 0
    assert 0 < cfg.limits.max_order_pct <= cfg.limits.max_position_pct
    assert cfg.limits.max_position_pct <= cfg.limits.max_total_exposure_pct
    assert cfg.limits.leverage_allowed is False


def test_risk_config_is_immutable() -> None:
    """R10 : aucune donnée externe ne peut modifier les limites après chargement."""
    cfg = load_risk_config()
    with pytest.raises(ValidationError):
        cfg.limits.max_order_pct = 1.0  # type: ignore[misc]


def test_risk_config_rejects_absurd_values() -> None:
    with pytest.raises(ValidationError):
        RiskConfig(
            capital={"initial": -5},
            limits={
                "max_order_pct": 2.0,
                "max_position_pct": 0.2,
                "max_total_exposure_pct": 0.6,
                "max_daily_loss_pct": 0.03,
                "max_drawdown_pct": 0.15,
                "leverage_allowed": False,
            },
            circuit_breakers={
                "max_consecutive_losses": 5,
                "pause_after_losses_minutes": 240,
                "max_hourly_loss_pct": 0.02,
                "max_api_errors_per_hour": 30,
                "reconciliation_tolerance_pct": 0.01,
            },
        )


def test_exchange_config_live_locked_by_default() -> None:
    """R6 : le live trading est verrouillé par défaut."""
    cfg = load_exchange_config()
    assert cfg.exchange.mode == "paper"
    assert cfg.exchange.live_trading is False


def test_strategies_config_loads() -> None:
    cfg = load_strategies_config()
    assert isinstance(cfg.strategies, tuple)
