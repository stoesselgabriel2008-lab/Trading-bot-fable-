"""Interface commune des stratégies (système de plugins).

Contrat (cf. docs/ARCHITECTURE.md) :
- une stratégie reçoit des OHLCV et retourne des POIDS CIBLES ∈ [0, 1] ;
- la valeur au timestamp t ne dépend que des bougies ≤ t (anti-lookahead) —
  le décalage d'exécution t+1 est appliqué par le moteur, jamais ici ;
- une stratégie ne touche ni à l'exécution ni au risque.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar

import pandas as pd


class Strategy(ABC):
    """Classe de base de toutes les stratégies.

    Attributes:
        name: identifiant unique de l'instance (ex. "ema_cross_balanced_btc").
        params: paramètres effectifs de l'instance.
    """

    #: Espace de paramètres documenté de la famille : {param: (min, max, défaut)}.
    param_space: ClassVar[dict[str, tuple[float, float, float]]] = {}
    #: Presets nommés : {"conservative": {...}, "balanced": {...}, "aggressive": {...}}.
    presets: ClassVar[dict[str, dict[str, Any]]] = {}

    def __init__(self, name: str, params: dict[str, Any] | None = None) -> None:
        self.name = name
        self.params = dict(params or {})

    @abstractmethod
    def generate_targets(self, data: dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Calcule la matrice de poids cibles.

        Args:
            data: {symbol: DataFrame OHLCV indexé DatetimeIndex UTC croissant,
                   colonnes [open, high, low, close, volume], bougies CLÔTURÉES}.

        Returns:
            DataFrame (index = union des index d'entrée, colonnes = symboles),
            valeurs = poids cible ∈ [0, 1] (fraction du capital allouée à l'actif).
            NaN interdit (utiliser 0.0 tant que la stratégie n'est pas prête).
        """

    @classmethod
    def from_preset(cls, name: str, preset: str, **overrides: Any) -> Strategy:
        """Instancie la stratégie depuis un preset nommé (+ surcharges éventuelles)."""
        if preset not in cls.presets:
            raise KeyError(
                f"Preset inconnu '{preset}' pour {cls.__name__} — "
                f"disponibles : {sorted(cls.presets)}"
            )
        params = {**cls.presets[preset], **overrides}
        return cls(name=name, params=params)
