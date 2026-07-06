"""Chargement et validation de la configuration YAML via pydantic.

Les limites de risque (`risk.yaml`) sont validées strictement : toute valeur
aberrante (fraction hors [0, 1], capital négatif…) fait échouer le démarrage.
Aucune donnée externe ne peut modifier ces objets après chargement — les
modèles sont immuables (frozen), cf. règle R10.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"


class _FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


# --------------------------------------------------------------------------
# assets.yaml
# --------------------------------------------------------------------------
class Asset(_FrozenModel):
    symbol: str = Field(pattern=r"^[A-Z0-9]+/[A-Z0-9]+$")


class AssetsConfig(_FrozenModel):
    assets: tuple[Asset, ...]
    timeframes: tuple[str, ...]
    quote_currency: str


# --------------------------------------------------------------------------
# risk.yaml
# --------------------------------------------------------------------------
class CapitalConfig(_FrozenModel):
    initial: float = Field(gt=0)


class RiskLimits(_FrozenModel):
    max_order_pct: float = Field(gt=0, le=1)
    max_position_pct: float = Field(gt=0, le=1)
    max_total_exposure_pct: float = Field(gt=0, le=1)
    max_daily_loss_pct: float = Field(gt=0, le=1)
    max_drawdown_pct: float = Field(gt=0, le=1)
    leverage_allowed: bool


class CircuitBreakers(_FrozenModel):
    max_consecutive_losses: int = Field(gt=0)
    pause_after_losses_minutes: int = Field(gt=0)
    max_hourly_loss_pct: float = Field(gt=0, le=1)
    max_api_errors_per_hour: int = Field(gt=0)
    reconciliation_tolerance_pct: float = Field(ge=0, le=1)


class RiskConfig(_FrozenModel):
    capital: CapitalConfig
    limits: RiskLimits
    circuit_breakers: CircuitBreakers


# --------------------------------------------------------------------------
# exchange.yaml
# --------------------------------------------------------------------------
class ExchangeSection(_FrozenModel):
    id: str
    mode: Literal["paper", "testnet", "live"]
    live_trading: bool


class FeesConfig(_FrozenModel):
    maker: float = Field(ge=0, lt=0.05)
    taker: float = Field(ge=0, lt=0.05)


class SlippageConfig(_FrozenModel):
    base_bps: float = Field(ge=0)
    volume_impact: bool


class ExchangeConfig(_FrozenModel):
    exchange: ExchangeSection
    fees: FeesConfig
    slippage: SlippageConfig


# --------------------------------------------------------------------------
# strategies.yaml
# --------------------------------------------------------------------------
class StrategyEntry(_FrozenModel):
    name: str
    family: str
    preset: str = "balanced"
    symbols: tuple[str, ...] = ()
    timeframe: str = "4h"
    params: dict[str, float | int | str | bool] = Field(default_factory=dict)

    model_config = ConfigDict(frozen=True, extra="forbid")


class StrategiesConfig(_FrozenModel):
    strategies: tuple[StrategyEntry, ...] = ()


# --------------------------------------------------------------------------
# Chargement
# --------------------------------------------------------------------------
def _load_yaml(path: Path) -> dict:
    with open(path, encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"Config invalide (dictionnaire attendu) : {path}")
    return data


def load_assets_config(config_dir: Path = CONFIG_DIR) -> AssetsConfig:
    return AssetsConfig(**_load_yaml(config_dir / "assets.yaml"))


def load_risk_config(config_dir: Path = CONFIG_DIR) -> RiskConfig:
    return RiskConfig(**_load_yaml(config_dir / "risk.yaml"))


def load_exchange_config(config_dir: Path = CONFIG_DIR) -> ExchangeConfig:
    return ExchangeConfig(**_load_yaml(config_dir / "exchange.yaml"))


def load_strategies_config(config_dir: Path = CONFIG_DIR) -> StrategiesConfig:
    return StrategiesConfig(**_load_yaml(config_dir / "strategies.yaml"))
