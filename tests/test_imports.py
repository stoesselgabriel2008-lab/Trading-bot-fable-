"""Tests d'import des squelettes de modules (Phase 2)."""

import importlib

import pytest

MODULES = [
    "src.data.fetcher",
    "src.data.storage",
    "src.data.quality",
    "src.strategies.base",
    "src.backtest.engine",
    "src.backtest.metrics",
    "src.validation.splits",
    "src.validation.walkforward",
    "src.validation.sensitivity",
    "src.validation.montecarlo",
    "src.validation.dsr",
    "src.validation.regimes",
    "src.risk.manager",
    "src.risk.breakers",
    "src.execution.executor",
    "src.execution.broker",
    "src.execution.state",
    "src.execution.scheduler",
    "src.monitoring.journal",
    "src.monitoring.reporting",
    "src.monitoring.alerts",
    "src.utils.config",
    "src.utils.logging_setup",
]


@pytest.mark.parametrize("module", MODULES)
def test_module_imports(module: str) -> None:
    importlib.import_module(module)


def test_strategy_is_abstract() -> None:
    from src.strategies.base import Strategy

    with pytest.raises(TypeError):
        Strategy(name="x")  # type: ignore[abstract]


def test_strategy_preset_mechanism() -> None:
    from typing import Any, ClassVar

    import pandas as pd

    from src.strategies.base import Strategy

    class Dummy(Strategy):
        presets: ClassVar[dict[str, dict[str, Any]]] = {"balanced": {"n": 3}}

        def generate_targets(self, data: dict[str, pd.DataFrame]) -> pd.DataFrame:
            return pd.DataFrame()

    s = Dummy.from_preset("d", "balanced", n=5)
    assert s.params == {"n": 5}
    with pytest.raises(KeyError):
        Dummy.from_preset("d", "inexistant")
