"""Batterie de validation anti-illusion complète (Phase 6).

Usage : make validate
Produit : docs/VALIDATION_REPORT.md — verdicts honnêtes par couple stratégie × actif.

Périmètre : 7 familles × {BTC, ETH, SOL} en 1d (momentum_xs : portefeuille entier).
Walk-forward : IS 730 bougies (~2 ans) / OOS 182 (~6 mois), rolling.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data.storage import DATA_DIR, dataset_path, load
from src.strategies.families import FAMILIES, VolTargetOverlay, with_vol_target
from src.utils.config import load_assets_config, load_exchange_config
from src.utils.logging_setup import setup_logging
from src.validation.protocol import CoupleVerdict, validate_couple

TIMEFRAME = "1d"
IS_BARS, OOS_BARS = 730, 182


def render_report(verdicts: list[CoupleVerdict], elapsed_s: float, total_configs: int) -> str:
    n_ok = sum(1 for v in verdicts if v.verdict == "VALIDÉE")
    lines = [
        "# VALIDATION REPORT — verdicts par couple stratégie × actif",
        "",
        f"Protocole complet (docs/reports/PHASE_6.md) exécuté en {elapsed_s:.0f}s.",
        f"**{n_ok} couple(s) VALIDÉ(S) / {len(verdicts)} testés — "
        f"{len(verdicts) - n_ok} rejetés.** Rappel : il est statistiquement NORMAL que la",
        "majorité échoue ; le dire est la preuve que le protocole fonctionne.",
        "",
        f"Configurations testées au total (comptage honnête, tous couples) : **{total_configs}**.",
        "Coûts stressés appliqués partout pour les critères : frais ×1,5, slippage ×2.",
        "",
        "Deux passes : (1) les 7 familles brutes ; (2) suffixe `_VT` = **l'UNIQUE itération",
        "de refonte autorisée par R3** (overlay volatility targeting 25 %/30 bougies, paramètres",
        "fixes, motivée par la recherche Phase 1 et le mode d'échec dominant de la passe 1 —",
        "drawdowns > 30 %). Les verdicts de la passe 2 sont DÉFINITIFS : aucune autre",
        "itération n'est permise.",
        "",
        "## Synthèse",
        "",
        "| Stratégie | Périmètre | Verdict | Ret. OOS stress | Sharpe OOS | Max DD | PF | Fen.+ | Pctl vs aléa | DSR | P(hasard) |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for v in verdicts:
        m = v.wf_stressed.oos_metrics if v.wf_stressed else None
        lines.append(
            f"| {v.strategy} | {v.scope} | **{v.verdict}** "
            f"| {m.total_return:+.1%} | {m.sharpe:.2f} | {m.max_drawdown:.1%} "
            f"| {m.profit_factor:.2f} | {v.wf_stressed.pct_windows_positive:.0%} "
            f"| {v.random_percentile:.0f} | {v.dsr['dsr']:.2f} | {v.dsr['p_random']:.0%} |"
            if m
            else f"| {v.strategy} | {v.scope} | **{v.verdict}** | - | - | - | - | - | - | - | - |"
        )

    lines += ["", "## Détail par couple", ""]
    for v in verdicts:
        lines += [f"### {v.strategy} × {v.scope} — {v.verdict}", ""]
        if v.chosen_params:
            lines.append(f"- Paramètres retenus (mode du walk-forward) : `{v.chosen_params}`")
            lines.append(f"- Configurations testées pour ce couple : {v.n_configs_tested}")
        if v.wf_stressed and v.wf_stressed.oos_metrics:
            m = v.wf_stressed.oos_metrics
            lines.append(
                f"- OOS stressé : rendement {m.total_return:+.1%}, annualisé {m.annualized_return:+.1%}, "
                f"Sharpe {m.sharpe:.2f}, Sortino {m.sortino:.2f}, Calmar {m.calmar:.2f}, "
                f"max DD {m.max_drawdown:.1%} ({m.max_drawdown_duration_bars} bougies), "
                f"PF {m.profit_factor:.2f}, win rate {m.win_rate:.0%}, "
                f"{m.n_trades} trades, expectancy {m.expectancy_per_trade:+.3%}"
            )
            lines.append(
                f"- Fenêtres WF positives (stress) : {v.wf_stressed.pct_windows_positive:.0%} "
                f"({len(v.wf_stressed.windows)} fenêtres)"
            )
        if v.sensitivity is not None:
            s = v.sensitivity
            lines.append(
                f"- Sensibilité : Sharpe optimal {s.base_sharpe:.2f}, médiane des voisins "
                f"{s.neighbor_median_sharpe:.2f} -> {'robuste' if s.is_robust else 'îlot étroit (REJET)'}"
            )
        if v.montecarlo is not None:
            mc = v.montecarlo
            lines.append(
                f"- Monte Carlo ({mc.n_draws} tirages, {mc.n_trades} trades) : rendement "
                f"IC95 [{mc.ret_ci_low:+.1%}, {mc.ret_ci_high:+.1%}], DD p95 {mc.dd_p95:.1%}, "
                f"P(rendement<0) = {mc.prob_negative:.0%}"
            )
        lines.append(
            f"- DSR : SR̂={v.dsr['sr_hat']:.4f}, SR₀={v.dsr['sr0']:.4f}, DSR={v.dsr['dsr']:.2f} "
            f"-> **probabilité que le résultat soit dû au hasard/sélection : {v.dsr['p_random']:.0%}**"
        )
        if v.regime_table is not None:
            rt = v.regime_table
            lines.append(
                "- Par régime (OOS stressé) : "
                + ", ".join(
                    f"{reg} {rt.loc[reg, 'cum_return']:+.1%} ({rt.loc[reg, 'n_bars']} bougies)"
                    for reg in rt.index
                )
            )
        lines.append(
            f"- Segment validation (15 %, coûts stressés) : {v.val_return_stressed:+.1%} ; "
            f"percentile vs 200 baselines aléatoires calibrées : {v.random_percentile:.0f} ; "
            f"Calmar {v.calmar_val:.2f} vs B&H {v.calmar_bh_val:.2f}"
        )
        if v.criteria:
            failed = [k for k, ok in v.criteria.items() if not ok]
            passed = [k for k, ok in v.criteria.items() if ok]
            lines.append(f"- Critères OK : {', '.join(passed) or 'aucun'}")
            lines.append(f"- Critères ÉCHOUÉS : {', '.join(failed) or 'aucun'}")
        if v.final_test_return is not None:
            lines.append(
                f"- **TEST FINAL (15 % jamais touchés, exécuté une seule fois) : "
                f"{v.final_test_return:+.1%}**"
            )
        lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    logger = setup_logging()
    t0 = time.time()
    assets = load_assets_config()
    ex_cfg = load_exchange_config()
    source = ex_cfg.data.historical_source

    data = {}
    for a in assets.assets:
        df = load(dataset_path(source, a.symbol, TIMEFRAME, DATA_DIR))
        if df is None:
            logger.error("données absentes pour %s — lancer make fetch-data", a.symbol)
            return 1
        data[a.symbol] = df

    verdicts: list[CoupleVerdict] = []

    def run_pass(families: dict[str, type], label: str) -> None:
        for name, cls in families.items():
            scopes = (
                [("PORTFOLIO", data)]
                if name.startswith("momentum_xs")
                else [(sym, {sym: df}) for sym, df in data.items()]
            )
            for scope, scoped_data in scopes:
                logger.info("validation [%s] %s × %s ...", label, name, scope)
                verdicts.append(
                    validate_couple(
                        cls,
                        scope,
                        scoped_data,
                        ex_cfg.fees,
                        ex_cfg.slippage,
                        TIMEFRAME,
                        IS_BARS,
                        OOS_BARS,
                    )
                )

    base_families = {n: c for n, c in FAMILIES.items() if c is not VolTargetOverlay}
    run_pass(base_families, "passe 1 — familles brutes")

    # REFONTE UNIQUE (règle R3) : overlay de volatility targeting à paramètres
    # FIXES (25 % annuel / fenêtre 30), appliqué uniformément à toutes les familles.
    # Motivée par la recherche Phase 1 (RESEARCH.md §3/§5) et par le mode d'échec
    # dominant de la passe 1 (drawdowns > 30 %). Aucune autre itération n'est
    # autorisée : les verdicts de cette passe sont DÉFINITIFS.
    vt_families = {f"{n}_vt": with_vol_target(c) for n, c in base_families.items()}
    run_pass(vt_families, "passe 2 — refonte unique vol-target")

    total_configs = sum(v.n_configs_tested for v in verdicts)
    out = Path(__file__).resolve().parents[1] / "docs" / "VALIDATION_REPORT.md"
    out.write_text(render_report(verdicts, time.time() - t0, total_configs), encoding="utf-8")
    logger.info("rapport écrit : %s (%.0fs)", out, time.time() - t0)
    n_ok = sum(1 for v in verdicts if v.verdict == "VALIDÉE")
    logger.info("VERDICTS : %d validées / %d rejetées", n_ok, len(verdicts) - n_ok)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
