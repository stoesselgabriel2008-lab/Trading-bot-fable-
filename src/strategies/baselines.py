"""Baselines « juges de paix » (Phase 5).

- BuyAndHold : détenir l'actif en permanence — l'étalon passif.
- RandomTiming : entrées/sorties aléatoires calibrées sur la fréquence de trades
  d'une stratégie cible : P(switch) = 1/D où D = durée moyenne de détention
  (cf. RESEARCH.md §4). Toute stratégie qui ne bat pas NETTEMENT la distribution
  de cette baseline après coûts est du bruit.
"""

from __future__ import annotations

from typing import Any, ClassVar

import numpy as np
import pandas as pd

from src.strategies.base import Strategy


class BuyAndHold(Strategy):
    """Poids 1 en permanence sur chaque actif (dès sa première cotation)."""

    presets: ClassVar[dict[str, dict[str, Any]]] = {"balanced": {}}

    def generate_targets(self, data: dict[str, pd.DataFrame]) -> pd.DataFrame:
        out = pd.DataFrame({sym: pd.Series(1.0, index=df.index) for sym, df in data.items()})
        return out.fillna(0.0)


class RandomTiming(Strategy):
    """Long/flat aléatoire, calibré : P(passer long) = P(sortir) = 1/hold_bars.

    Espérance d'exposition ≈ 50 %, durée moyenne de détention ≈ ``hold_bars`` —
    à calibrer sur la stratégie comparée. ``seed`` rend chaque tirage reproductible.
    """

    param_space: ClassVar = {"hold_bars": (2, 500, 20)}
    presets: ClassVar[dict[str, dict[str, Any]]] = {"balanced": {"hold_bars": 20, "seed": 0}}

    def generate_targets(self, data: dict[str, pd.DataFrame]) -> pd.DataFrame:
        hold = max(2, int(self.params.get("hold_bars", 20)))
        seed = int(self.params.get("seed", 0))
        p_switch = 1.0 / hold
        out = {}
        for k, (sym, df) in enumerate(sorted(data.items())):
            rng = np.random.default_rng(seed * 10_007 + k)
            switches = rng.random(len(df)) < p_switch
            # état long/flat qui bascule à chaque switch (cumsum modulo 2)
            state = np.cumsum(switches) % 2
            out[sym] = pd.Series(state.astype(float), index=df.index)
        return pd.DataFrame(out).fillna(0.0)


BASELINES: dict[str, type[Strategy]] = {
    "buy_hold": BuyAndHold,
    "random_timing": RandomTiming,
}
