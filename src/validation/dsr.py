"""Deflated Sharpe Ratio — Bailey & López de Prado.

Formules vérifiées le 2026-07-06 (2 sources : Wikipedia « Deflated Sharpe ratio »
et le papier original, davidhbailey.com/dhbpapers/deflated-sharpe.pdf — cf.
docs/RESEARCH.md §4) :

    PSR(SR*) = Φ( (SR̂ − SR*) · √(T−1) / √(1 − γ₃·SR̂ + ((γ₄−1)/4)·SR̂²) )

    SR₀ = √V[SR̂ₙ] · ( (1−γ)·Φ⁻¹(1 − 1/N) + γ·Φ⁻¹(1 − 1/(N·e)) )

    DSR = PSR(SR₀)

où SR̂ est le Sharpe NON annualisé (par bougie), T la longueur de l'échantillon,
γ₃/γ₄ le skewness/kurtosis des rendements, N le nombre d'essais, V[SR̂ₙ] la
variance des Sharpe entre essais, γ ≈ 0,5772 (Euler-Mascheroni).
Interprétation : probabilité que le vrai Sharpe soit > 0 malgré la sélection
parmi N essais. DSR ≥ 0,95 = significatif à 95 %.
"""

from __future__ import annotations

import math
from statistics import NormalDist

import numpy as np
import pandas as pd

_NORM = NormalDist()
EULER_MASCHERONI = 0.5772156649015329


def sharpe_non_annualized(returns: pd.Series) -> float:
    std = returns.std(ddof=1)
    if std == 0 or len(returns) < 2:
        return 0.0
    return float(returns.mean() / std)


def probabilistic_sharpe_ratio(returns: pd.Series, sr_benchmark: float) -> float:
    """PSR : probabilité que le vrai Sharpe dépasse ``sr_benchmark``."""
    t = len(returns)
    if t < 3:
        return 0.0
    sr = sharpe_non_annualized(returns)
    skew = float(returns.skew())
    kurt = float(returns.kurtosis()) + 3.0  # pandas donne l'excès de kurtosis
    denom = 1.0 - skew * sr + ((kurt - 1.0) / 4.0) * sr**2
    if denom <= 0:
        return 0.0
    z = (sr - sr_benchmark) * math.sqrt(t - 1) / math.sqrt(denom)
    return float(_NORM.cdf(z))


def expected_max_sharpe(n_trials: int, var_sharpe: float) -> float:
    """SR₀ : Sharpe max attendu parmi ``n_trials`` stratégies SANS aucun talent."""
    if n_trials <= 1 or var_sharpe <= 0:
        return 0.0
    g = EULER_MASCHERONI
    return float(
        math.sqrt(var_sharpe)
        * (
            (1 - g) * _NORM.inv_cdf(1 - 1 / n_trials)
            + g * _NORM.inv_cdf(1 - 1 / (n_trials * math.e))
        )
    )


def deflated_sharpe_ratio(
    returns: pd.Series, n_trials: int, trial_sharpes: list[float] | None = None
) -> dict[str, float]:
    """DSR complet.

    Args:
        returns: rendements par bougie de la stratégie SÉLECTIONNÉE (OOS).
        n_trials: nombre TOTAL de configurations testées (comptage honnête).
        trial_sharpes: Sharpe (non annualisés) de tous les essais, pour V[SR̂ₙ] ;
            à défaut, la variance est estimée sur les rendements sélectionnés
            (approximation conservatrice documentée).

    Returns:
        {"sr_hat", "sr0", "dsr", "p_random"} — p_random = 1 − DSR, probabilité
        que le résultat soit dû au hasard/sélection.
    """
    sr_hat = sharpe_non_annualized(returns)
    if trial_sharpes is not None and len(trial_sharpes) > 1:
        var_sharpe = float(np.var(trial_sharpes, ddof=1))
    else:
        # Approximation : variance de l'estimateur du SR ≈ (1 + SR²/2) / T.
        var_sharpe = (1 + sr_hat**2 / 2) / max(len(returns), 2)
    sr0 = expected_max_sharpe(n_trials, var_sharpe)
    dsr = probabilistic_sharpe_ratio(returns, sr0)
    return {"sr_hat": sr_hat, "sr0": sr0, "dsr": dsr, "p_random": 1.0 - dsr}
