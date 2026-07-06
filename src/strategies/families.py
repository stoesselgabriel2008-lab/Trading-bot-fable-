"""Les familles de stratégies (Phase 5) — cf. docs/RESEARCH.md §3.

Chaque famille implémente l'interface Strategy : OHLCV -> poids cibles ∈ [0, 1].
Aucune famille ne touche à l'exécution ni au risque. Les presets suivent la
convention conservative / balanced / aggressive.
"""

from __future__ import annotations

from typing import Any, ClassVar

import numpy as np
import pandas as pd

from src.strategies.base import Strategy
from src.strategies.indicators import atr, donchian, ema, realized_vol, rsi, sma, zscore


def _per_symbol(data: dict[str, pd.DataFrame], fn) -> pd.DataFrame:
    """Applique ``fn(df) -> Series de poids`` à chaque actif et assemble la matrice."""
    out = pd.DataFrame({sym: fn(df) for sym, df in data.items()})
    return out.fillna(0.0).clip(0.0, 1.0)


class EmaCross(Strategy):
    """Trend following : long quand EMA(fast) > EMA(slow), avec filtre de tendance
    optionnel (close > SMA(trend_filter)) pour limiter les whipsaws en range."""

    param_space: ClassVar = {
        "fast": (5, 50, 20),
        "slow": (20, 200, 50),
        "trend_filter": (0, 400, 200),
    }
    presets: ClassVar[dict[str, dict[str, Any]]] = {
        "conservative": {"fast": 20, "slow": 100, "trend_filter": 200},
        "balanced": {"fast": 20, "slow": 50, "trend_filter": 200},
        "aggressive": {"fast": 10, "slow": 30, "trend_filter": 0},
    }

    def generate_targets(self, data: dict[str, pd.DataFrame]) -> pd.DataFrame:
        fast, slow = int(self.params["fast"]), int(self.params["slow"])
        tf = int(self.params.get("trend_filter", 0))

        def signal(df: pd.DataFrame) -> pd.Series:
            long = ema(df["close"], fast) > ema(df["close"], slow)
            if tf > 0:
                long &= df["close"] > sma(df["close"], tf)
            return long.astype(float)

        return _per_symbol(data, signal)


class DonchianBreakout(Strategy):
    """Breakout de canal de Donchian (Turtle) : entrée au-dessus du plus haut N,
    sortie sous le plus bas M (M < N)."""

    param_space: ClassVar = {"entry": (10, 100, 20), "exit": (5, 50, 10)}
    presets: ClassVar[dict[str, dict[str, Any]]] = {
        "conservative": {"entry": 55, "exit": 20},
        "balanced": {"entry": 20, "exit": 10},
        "aggressive": {"entry": 10, "exit": 5},
    }

    def generate_targets(self, data: dict[str, pd.DataFrame]) -> pd.DataFrame:
        n_in, n_out = int(self.params["entry"]), int(self.params["exit"])

        def signal(df: pd.DataFrame) -> pd.Series:
            upper, _ = donchian(df, n_in)
            _, lower = donchian(df, n_out)
            close = df["close"]
            raw = pd.Series(np.nan, index=df.index)
            raw[close > upper] = 1.0
            raw[close < lower] = 0.0
            return raw.ffill().fillna(0.0)

        return _per_symbol(data, signal)


class MeanReversion(Strategy):
    """Mean reversion : entrée quand RSI < seuil ET z-score < -z ; sortie quand
    RSI repasse au-dessus de 50 ou après ``time_stop`` bougies (cf. RESEARCH §3 :
    time-stop obligatoire, la réversion qui ne vient pas se coupe)."""

    param_space: ClassVar = {
        "rsi_period": (5, 30, 14),
        "rsi_entry": (10, 40, 30),
        "z_window": (10, 60, 20),
        "z_entry": (-3.5, -1.0, -2.0),
        "time_stop": (3, 30, 10),
    }
    presets: ClassVar[dict[str, dict[str, Any]]] = {
        "conservative": {
            "rsi_period": 14,
            "rsi_entry": 25,
            "z_window": 20,
            "z_entry": -2.5,
            "time_stop": 8,
        },
        "balanced": {
            "rsi_period": 14,
            "rsi_entry": 30,
            "z_window": 20,
            "z_entry": -2.0,
            "time_stop": 10,
        },
        "aggressive": {
            "rsi_period": 7,
            "rsi_entry": 35,
            "z_window": 15,
            "z_entry": -1.5,
            "time_stop": 15,
        },
    }

    def generate_targets(self, data: dict[str, pd.DataFrame]) -> pd.DataFrame:
        p = self.params

        def signal(df: pd.DataFrame) -> pd.Series:
            r = rsi(df["close"], int(p["rsi_period"]))
            z = zscore(df["close"], int(p["z_window"]))
            entry = (r < float(p["rsi_entry"])) & (z < float(p["z_entry"]))
            exit_ = r > 50
            pos = np.zeros(len(df))
            held = 0
            in_pos = False
            entry_arr, exit_arr = entry.to_numpy(), exit_.to_numpy()
            for i in range(len(df)):
                if in_pos:
                    held += 1
                    if exit_arr[i] or held >= int(p["time_stop"]):
                        in_pos = False
                    else:
                        pos[i] = 1.0
                if not in_pos and entry_arr[i]:
                    in_pos = True
                    held = 0
                    pos[i] = 1.0
            return pd.Series(pos, index=df.index)

        return _per_symbol(data, signal)


class AtrBreakout(Strategy):
    """Breakout de volatilité : long si close > plus haut(N) précédent + k×ATR ;
    sortie sous un trailing stop à m×ATR sous le plus haut atteint en position."""

    param_space: ClassVar = {
        "lookback": (10, 100, 20),
        "k_entry": (0.0, 2.0, 0.5),
        "k_exit": (1.0, 5.0, 2.5),
    }
    presets: ClassVar[dict[str, dict[str, Any]]] = {
        "conservative": {"lookback": 55, "k_entry": 1.0, "k_exit": 3.0},
        "balanced": {"lookback": 20, "k_entry": 0.5, "k_exit": 2.5},
        "aggressive": {"lookback": 10, "k_entry": 0.25, "k_exit": 2.0},
    }

    def generate_targets(self, data: dict[str, pd.DataFrame]) -> pd.DataFrame:
        p = self.params

        def signal(df: pd.DataFrame) -> pd.Series:
            a = atr(df, 14)
            hh = df["high"].rolling(int(p["lookback"])).max().shift(1)
            entry = (df["close"] > hh + float(p["k_entry"]) * a).to_numpy()
            close = df["close"].to_numpy()
            atr_np = a.to_numpy()
            pos = np.zeros(len(df))
            in_pos, peak = False, 0.0
            for i in range(len(df)):
                if in_pos:
                    peak = max(peak, close[i])
                    if close[i] < peak - float(p["k_exit"]) * atr_np[i]:
                        in_pos = False
                    else:
                        pos[i] = 1.0
                if not in_pos and entry[i]:
                    in_pos, peak = True, close[i]
                    pos[i] = 1.0
            return pd.Series(pos, index=df.index)

        return _per_symbol(data, signal)


class CrossSectionalMomentum(Strategy):
    """Momentum cross-sectional : à chaque rebalancement, long sur les ``top_k``
    actifs au meilleur rendement ``lookback`` bougies — à condition qu'il soit
    positif (filtre absolu, protège des bear markets généralisés)."""

    param_space: ClassVar = {
        "lookback": (20, 365, 90),
        "top_k": (1, 3, 2),
        "rebalance_every": (1, 30, 7),
    }
    presets: ClassVar[dict[str, dict[str, Any]]] = {
        "conservative": {"lookback": 180, "top_k": 1, "rebalance_every": 14},
        "balanced": {"lookback": 90, "top_k": 2, "rebalance_every": 7},
        "aggressive": {"lookback": 30, "top_k": 2, "rebalance_every": 3},
    }

    def generate_targets(self, data: dict[str, pd.DataFrame]) -> pd.DataFrame:
        lb = int(self.params["lookback"])
        top_k = int(self.params["top_k"])
        every = int(self.params["rebalance_every"])
        closes = pd.DataFrame({sym: df["close"] for sym, df in data.items()}).sort_index()
        mom = closes.pct_change(lb)
        ranks = mom.rank(axis=1, ascending=False)
        selected = (ranks <= top_k) & (mom > 0)
        weights = selected.astype(float) / top_k
        # Rebalancement seulement toutes les ``every`` bougies (réduit le turnover).
        keep = np.arange(len(weights)) % every == 0
        weights = weights.where(pd.Series(keep, index=weights.index), np.nan).ffill()
        return weights.fillna(0.0).clip(0.0, 1.0)


class ConditionalDca(Strategy):
    """DCA conditionnel : exposition d'autant plus forte que le prix est décoté
    par rapport à sa SMA longue (accumulation en baisse, allègement en euphorie)."""

    param_space: ClassVar = {"ma_window": (50, 400, 200), "max_discount": (0.1, 0.6, 0.3)}
    presets: ClassVar[dict[str, dict[str, Any]]] = {
        "conservative": {"ma_window": 200, "max_discount": 0.4},
        "balanced": {"ma_window": 200, "max_discount": 0.3},
        "aggressive": {"ma_window": 100, "max_discount": 0.2},
    }

    def generate_targets(self, data: dict[str, pd.DataFrame]) -> pd.DataFrame:
        p = self.params

        def signal(df: pd.DataFrame) -> pd.Series:
            ma = sma(df["close"], int(p["ma_window"]))
            discount = (ma - df["close"]) / ma  # >0 si sous la moyenne
            w = 0.5 + discount / float(p["max_discount"]) * 0.5
            return w.clip(0.0, 1.0)

        return _per_symbol(data, signal)


class GridRange(Strategy):
    """Grid trading borné : dans un range défini autour d'une SMA (±range_pct),
    l'exposition augmente vers le bas de la grille et diminue vers le haut.
    STOP GLOBAL : sortie totale si le prix casse le bas du range (breakout
    baissier = le poison des grilles, cf. RESEARCH §3)."""

    param_space: ClassVar = {"ma_window": (20, 200, 50), "range_pct": (0.05, 0.4, 0.15)}
    presets: ClassVar[dict[str, dict[str, Any]]] = {
        "conservative": {"ma_window": 100, "range_pct": 0.20},
        "balanced": {"ma_window": 50, "range_pct": 0.15},
        "aggressive": {"ma_window": 30, "range_pct": 0.10},
    }

    def generate_targets(self, data: dict[str, pd.DataFrame]) -> pd.DataFrame:
        p = self.params

        def signal(df: pd.DataFrame) -> pd.Series:
            center = sma(df["close"], int(p["ma_window"]))
            rng = float(p["range_pct"])
            pos_in_range = (df["close"] - center) / (center * rng)  # -1 bas .. +1 haut
            w = (1.0 - pos_in_range) / 2.0  # 1 en bas de grille, 0 en haut
            w = w.where(pos_in_range.abs() <= 1.0, 0.0)  # stop global hors range
            return w.clip(0.0, 1.0)

        return _per_symbol(data, signal)


class VolTargetOverlay(Strategy):
    """Overlay de volatility targeting : multiplie les poids d'une stratégie
    sous-jacente par min(1, vol_cible / vol_réalisée) — jamais de levier."""

    param_space: ClassVar = {"target_vol_annual": (0.1, 1.0, 0.4), "vol_window": (10, 60, 30)}
    presets: ClassVar[dict[str, dict[str, Any]]] = {
        "conservative": {"target_vol_annual": 0.25, "vol_window": 30},
        "balanced": {"target_vol_annual": 0.40, "vol_window": 30},
        "aggressive": {"target_vol_annual": 0.60, "vol_window": 20},
    }

    def __init__(
        self,
        name: str,
        params: dict | None = None,
        inner: Strategy | None = None,
        periods_per_year: int = 365,
    ) -> None:
        super().__init__(name, params)
        if inner is None:
            raise ValueError("VolTargetOverlay requiert une stratégie sous-jacente (inner)")
        self.inner = inner
        self.periods_per_year = periods_per_year

    def generate_targets(self, data: dict[str, pd.DataFrame]) -> pd.DataFrame:
        base = self.inner.generate_targets(data)
        window = int(self.params["vol_window"])
        target_per_bar = float(self.params["target_vol_annual"]) / np.sqrt(self.periods_per_year)
        scales = {}
        for sym, df in data.items():
            rv = realized_vol(df["close"], window)
            scales[sym] = (target_per_bar / rv).clip(upper=1.0)
        scale = pd.DataFrame(scales).reindex(base.index)
        return (base * scale).fillna(0.0).clip(0.0, 1.0)


FAMILIES: dict[str, type[Strategy]] = {
    "ema_cross": EmaCross,
    "donchian": DonchianBreakout,
    "mean_reversion": MeanReversion,
    "atr_breakout": AtrBreakout,
    "momentum_xs": CrossSectionalMomentum,
    "dca_conditional": ConditionalDca,
    "grid_range": GridRange,
    "vol_target_overlay": VolTargetOverlay,
}
