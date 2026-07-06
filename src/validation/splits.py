"""Découpage temporel strict 70/15/15 (Phase 6, étape 1).

Le segment de TEST FINAL (les derniers 15 %) n'est touché qu'UNE seule fois,
tout à la fin, pour les seules stratégies survivantes — aucun ajustement
autorisé ensuite (règle du protocole, mission §9.1).
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class Split:
    dev: pd.DataFrame  # ~70 % — développement + walk-forward
    validation: pd.DataFrame  # ~15 % — confirmation hors optimisation
    test_final: pd.DataFrame  # ~15 % — touché UNE fois, à la fin


def split_frame(df: pd.DataFrame, dev: float = 0.70, val: float = 0.15) -> Split:
    n = len(df)
    i_dev = int(n * dev)
    i_val = int(n * (dev + val))
    return Split(dev=df.iloc[:i_dev], validation=df.iloc[i_dev:i_val], test_final=df.iloc[i_val:])


def split_data(
    data: dict[str, pd.DataFrame], dev: float = 0.70, val: float = 0.15
) -> tuple[dict[str, pd.DataFrame], dict[str, pd.DataFrame], dict[str, pd.DataFrame]]:
    """Coupe chaque actif sur des DATES communes (celles de l'actif le plus long),
    pour que dev/val/test soient les mêmes périodes calendaires partout."""
    longest = max(data.values(), key=len)
    s = split_frame(longest, dev, val)
    d_end, v_end = s.dev.index[-1], s.validation.index[-1]
    dev_d = {k: df[df.index <= d_end] for k, df in data.items()}
    val_d = {k: df[(df.index > d_end) & (df.index <= v_end)] for k, df in data.items()}
    test_d = {k: df[df.index > v_end] for k, df in data.items()}
    return dev_d, val_d, test_d
