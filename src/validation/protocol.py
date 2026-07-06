"""Orchestrateur du protocole de validation anti-illusion (Phase 6).

Ordre imposé par la mission (§9), pour CHAQUE couple stratégie × actif :
1. découpage 70/15/15 ; 2. walk-forward ; 3. sensibilité ; 4. Monte Carlo ;
5. Deflated Sharpe (comptage honnête) ; 6. analyse par régime ; 7. stress des
coûts (frais ×1,5, slippage ×2) ; 8. critères de survie ; 9. verdict.

Le segment de test final n'est exécuté qu'UNE fois, pour les seuls survivants,
sans aucun ajustement possible ensuite.

Critères de survie par défaut (mission §9.8) — évalués sur l'OOS walk-forward
à COÛTS STRESSÉS et sur le segment de validation :
  C1 rendement net OOS > 0 (coûts stressés)
  C2 Sharpe OOS ≥ 0,8
  C3 max drawdown OOS ≥ −30 %
  C4 profit factor OOS ≥ 1,15
  C5 ≥ 60 % de fenêtres walk-forward positives
  C6 bat significativement la baseline aléatoire (percentile ≥ 90 sur 200 tirages)
  C7 Calmar compétitif vs buy & hold (≥ 0,8 × Calmar B&H, segment validation)
  C8 robustesse aux paramètres (médiane des voisins ≥ 50 % du Sharpe optimal)
Le DSR et sa probabilité de hasard sont TOUJOURS rapportés (pas de seuil imposé
par la mission — reporté honnêtement).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from src.backtest.engine import CostModel, run_backtest
from src.backtest.metrics import PERIODS_PER_YEAR
from src.strategies.base import Strategy
from src.strategies.baselines import BuyAndHold, RandomTiming
from src.utils.config import FeesConfig, SlippageConfig
from src.utils.logging_setup import get_logger
from src.validation.dsr import deflated_sharpe_ratio
from src.validation.montecarlo import MonteCarloResult, bootstrap_trades
from src.validation.regimes import classify_regimes, returns_by_regime
from src.validation.sensitivity import SensitivityResult, sensitivity_analysis
from src.validation.splits import split_data
from src.validation.walkforward import (
    WalkForwardResult,
    grid_from_presets,
    walk_forward,
)

logger = get_logger("validation.protocol")

N_RANDOM_BASELINES = 200
RANDOM_PERCENTILE_REQUIRED = 90.0


@dataclass
class CoupleVerdict:
    strategy: str
    scope: str  # symbole ou "PORTFOLIO"
    chosen_params: dict[str, Any]
    n_configs_tested: int
    wf: WalkForwardResult | None
    wf_stressed: WalkForwardResult | None
    sensitivity: SensitivityResult | None
    montecarlo: MonteCarloResult | None
    dsr: dict[str, float]
    regime_table: pd.DataFrame | None
    val_return_stressed: float
    random_percentile: float
    calmar_val: float
    calmar_bh_val: float
    criteria: dict[str, bool] = field(default_factory=dict)
    verdict: str = "REJETÉE"
    reasons: list[str] = field(default_factory=list)
    final_test_return: float | None = None  # rempli UNE fois pour les survivants


def _chosen_params(wf: WalkForwardResult) -> dict[str, Any]:
    """Paramètres retenus = jeu le plus souvent choisi par le walk-forward."""
    counts = Counter(tuple(sorted(w.best_params.items())) for w in wf.windows)
    best = counts.most_common(1)[0][0]
    return dict(best)


def _segment_return(
    cls: type[Strategy],
    params: dict[str, Any],
    warmup: dict[str, pd.DataFrame],
    segment: dict[str, pd.DataFrame],
    cost: CostModel,
    timeframe: str,
) -> tuple[float, pd.Series]:
    """Rendement net sur un segment, avec warm-up (les indicateurs ont besoin
    d'historique) mais métriques mesurées sur le segment uniquement."""
    data = {
        sym: pd.concat([warmup.get(sym, pd.DataFrame()), segment[sym]])
        for sym in segment
        if len(segment[sym])
    }
    if not data:
        return 0.0, pd.Series(dtype=float)
    strat = cls(name=cls.__name__, params=params)
    res = run_backtest(data, strat.generate_targets(data), cost)
    rets = res.equity.pct_change().fillna(0.0)
    seg_start = min(df.index[0] for df in segment.values() if len(df))
    seg_rets = rets[rets.index >= seg_start]
    return float((1 + seg_rets).prod() - 1), seg_rets


def _calmar(returns: pd.Series, timeframe: str) -> float:
    if len(returns) < 10:
        return 0.0
    ppy = PERIODS_PER_YEAR[timeframe]
    equity = (1 + returns).cumprod()
    ann = float(equity.iloc[-1] ** (ppy / len(equity)) - 1)
    peak = equity.cummax()
    max_dd = float((equity / peak - 1).min())
    return ann / abs(max_dd) if max_dd < 0 else 0.0


def _random_baseline_percentile(
    segment: dict[str, pd.DataFrame],
    warmup: dict[str, pd.DataFrame],
    hold_bars: int,
    cost: CostModel,
    timeframe: str,
    observed_return: float,
) -> float:
    """Percentile du rendement observé dans la distribution de N baselines aléatoires
    calibrées (même durée moyenne de détention, mêmes coûts stressés)."""
    outcomes = []
    for seed in range(N_RANDOM_BASELINES):
        ret, _ = _segment_return(
            RandomTiming, {"hold_bars": hold_bars, "seed": seed}, warmup, segment, cost, timeframe
        )
        outcomes.append(ret)
    arr = np.asarray(outcomes)
    return float((arr < observed_return).mean() * 100.0)


def validate_couple(
    cls: type[Strategy],
    scope: str,
    data: dict[str, pd.DataFrame],
    fees: FeesConfig,
    slippage: SlippageConfig,
    timeframe: str,
    is_bars: int,
    oos_bars: int,
) -> CoupleVerdict:
    """Applique le protocole complet à un couple stratégie × actif (ou portefeuille)."""
    cost = CostModel.from_configs(fees, slippage)
    cost_stressed = CostModel.from_configs(
        fees, slippage, fee_multiplier=1.5, slippage_multiplier=2.0
    )

    # 1. Découpage 70/15/15 — le test final est mis de côté.
    dev, val, test = split_data(data)

    # 2. Walk-forward (coûts normaux) sur le segment de développement.
    wf = walk_forward(cls, dev, cost, timeframe, is_bars, oos_bars)
    if not wf.windows:
        return _rejected(cls, scope, "walk-forward impossible (historique insuffisant)")
    params = _chosen_params(wf)

    # 7. Stress des coûts : le MÊME walk-forward avec frais ×1,5 et slippage ×2.
    wf_s = walk_forward(cls, dev, cost_stressed, timeframe, is_bars, oos_bars)
    n_configs = wf.n_configs_tested + wf_s.n_configs_tested + len(grid_from_presets(cls))

    # 3. Sensibilité aux paramètres autour de l'optimum (sur le dev, coûts normaux).
    sens = sensitivity_analysis(cls, params, dev, cost, timeframe)
    n_configs += len(sens.grid)

    # 4. Monte Carlo sur les trades OOS stressés.
    mc = bootstrap_trades(wf_s.oos_trade_pnls)

    # 5. Deflated Sharpe Ratio — N = comptage honnête de TOUTES les configurations.
    dsr = deflated_sharpe_ratio(
        wf_s.oos_returns, n_trials=max(n_configs, 2), trial_sharpes=wf_s.trial_sharpes
    )

    # 6. Analyse par régime (sur l'OOS stressé, régimes du 1er actif du scope).
    ref_close = pd.concat([dev[s]["close"] for s in sorted(dev)], axis=1).mean(axis=1)
    regimes = classify_regimes(ref_close)
    regime_table = returns_by_regime(wf_s.oos_returns, regimes)

    # Segment de validation (15 %) : coûts stressés, warm-up = fin du dev.
    warmup = {s: df.iloc[-400:] for s, df in dev.items()}
    val_ret, val_rets = _segment_return(cls, params, warmup, val, cost_stressed, timeframe)

    # C6 : distribution de baselines aléatoires calibrées sur le même segment.
    avg_hold = _avg_hold_bars(wf_s)
    pct = _random_baseline_percentile(val, warmup, avg_hold, cost_stressed, timeframe, val_ret)

    # C7 : Calmar vs buy & hold sur le segment de validation.
    calmar_strat = _calmar(val_rets, timeframe)
    _, bh_rets = _segment_return(BuyAndHold, {}, warmup, val, cost_stressed, timeframe)
    calmar_bh = _calmar(bh_rets, timeframe)

    m = wf_s.oos_metrics
    criteria = {
        "C1_rendement_net_positif_stress": m.total_return > 0,
        "C2_sharpe_oos_min_0.8": m.sharpe >= 0.8,
        "C3_max_dd_max_30pct": m.max_drawdown >= -0.30,
        "C4_profit_factor_min_1.15": m.profit_factor >= 1.15,
        "C5_min_60pct_fenetres_positives": wf_s.pct_windows_positive >= 0.60,
        "C6_bat_baseline_aleatoire_p90": pct >= RANDOM_PERCENTILE_REQUIRED,
        "C7_calmar_competitif_vs_bh": calmar_strat >= 0.8 * calmar_bh,
        "C8_robustesse_parametres": sens.is_robust,
    }
    reasons = [k for k, ok in criteria.items() if not ok]
    verdict = "VALIDÉE" if not reasons else "REJETÉE"

    v = CoupleVerdict(
        strategy=cls.__name__,
        scope=scope,
        chosen_params=params,
        n_configs_tested=n_configs,
        wf=wf,
        wf_stressed=wf_s,
        sensitivity=sens,
        montecarlo=mc,
        dsr=dsr,
        regime_table=regime_table,
        val_return_stressed=val_ret,
        random_percentile=pct,
        calmar_val=calmar_strat,
        calmar_bh_val=calmar_bh,
        criteria=criteria,
        verdict=verdict,
        reasons=reasons,
    )

    # 9. Test final : exécuté UNE seule fois, pour les seuls survivants.
    if verdict == "VALIDÉE":
        warmup_t = {s: pd.concat([dev[s], val[s]]).iloc[-400:] for s in dev}
        v.final_test_return, _ = _segment_return(
            cls, params, warmup_t, test, cost_stressed, timeframe
        )

    logger.info(
        "%s × %s -> %s (%s)", cls.__name__, scope, verdict, ", ".join(reasons) or "tous critères OK"
    )
    return v


def _avg_hold_bars(wf: WalkForwardResult) -> int:
    n = len(wf.oos_trade_pnls)
    exposure_bars = len(wf.oos_returns[wf.oos_returns != 0])
    if n == 0 or exposure_bars == 0:
        return 20
    return max(2, min(500, exposure_bars // max(n, 1)))


def _rejected(cls: type[Strategy], scope: str, reason: str) -> CoupleVerdict:
    return CoupleVerdict(
        strategy=cls.__name__,
        scope=scope,
        chosen_params={},
        n_configs_tested=0,
        wf=None,
        wf_stressed=None,
        sensitivity=None,
        montecarlo=None,
        dsr={"sr_hat": 0, "sr0": 0, "dsr": 0, "p_random": 1.0},
        regime_table=None,
        val_return_stressed=0.0,
        random_percentile=0.0,
        calmar_val=0.0,
        calmar_bh_val=0.0,
        criteria={},
        verdict="REJETÉE",
        reasons=[reason],
    )
