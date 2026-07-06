"""Démarre le paper trading (usage : make paper).

⚠️ RAPPEL HONNÊTETÉ (ADR-004) : aucune stratégie n'a survécu à la validation
anti-illusion. Ce paper trading valide l'INFRASTRUCTURE (exécution, risque,
breakers, persistance, kill switch, shortfall) avec la meilleure candidate
REJETÉE, étiquetée « NON VALIDÉE — observation uniquement ». Aucun capital réel.

Options :
    --cycles N     mode démonstration : N cycles immédiats puis sortie
    --timeframe TF 1h par défaut (cycles horaires)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.execution.executor import PaperExecutor
from src.execution.scheduler import run_fast_cycles, run_scheduled
from src.strategies.families import DonchianBreakout, with_vol_target
from src.utils.config import (
    load_assets_config,
    load_exchange_config,
    load_risk_config,
)
from src.utils.logging_setup import setup_logging

STRATEGY_LABEL = (
    "DonchianBreakout_VT[balanced] — STRATÉGIE NON VALIDÉE (VALIDATION_REPORT.md) "
    "— observation d'infrastructure uniquement"
)


def build_executor(timeframe: str) -> PaperExecutor:
    assets = load_assets_config()
    ex_cfg = load_exchange_config()
    risk_cfg = load_risk_config()
    if ex_cfg.exchange.mode != "paper":
        raise SystemExit("Ce script ne lance que le mode paper (cf. RUNBOOK pour testnet).")
    cls = with_vol_target(DonchianBreakout)
    strategy = cls(name="donchian_vt_paper", params=DonchianBreakout.presets["balanced"])
    return PaperExecutor(
        strategy=strategy,
        symbols=[a.symbol for a in assets.assets],
        timeframe=timeframe,
        exchange_cfg=ex_cfg,
        risk_cfg=risk_cfg,
        strategy_label=STRATEGY_LABEL,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cycles", type=int, default=0, help="mode démo : N cycles immédiats")
    parser.add_argument("--timeframe", default="1h")
    args = parser.parse_args()

    logger = setup_logging()
    logger.info("=== PAPER TRADING START — %s ===", STRATEGY_LABEL)
    executor = build_executor(args.timeframe)

    def cycle() -> None:
        report = executor.run_cycle()
        logger.info(
            "cycle %s : %s (equity=%.2f) %s", report.ts, report.action, report.equity, report.detail
        )

    if args.cycles > 0:
        run_fast_cycles(cycle, args.cycles)
    else:
        run_scheduled(cycle, args.timeframe)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
