"""Génère le rapport quotidien + dashboard + exports CSV (usage : make report)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.backtest.engine import CostModel
from src.data.storage import DATA_DIR, dataset_path, load
from src.execution.state import StateStore
from src.monitoring.reporting import write_all_reports
from src.strategies.families import DonchianBreakout, with_vol_target
from src.utils.config import load_assets_config, load_exchange_config
from src.utils.logging_setup import setup_logging

STRATEGY_LABEL = (
    "DonchianBreakout_VT[balanced] — STRATÉGIE NON VALIDÉE (VALIDATION_REPORT.md) "
    "— observation d'infrastructure uniquement"
)


def main() -> int:
    logger = setup_logging()
    root = Path(__file__).resolve().parents[1]
    store = StateStore(root / "state" / "bot.sqlite")
    assets = load_assets_config()
    ex_cfg = load_exchange_config()

    # Référence backtest : même stratégie, 2 dernières années de 1d, mêmes coûts.
    data = {}
    for a in assets.assets:
        df = load(dataset_path(ex_cfg.data.historical_source, a.symbol, "1d", DATA_DIR))
        if df is not None:
            data[a.symbol] = df.iloc[-730:]
    cls = with_vol_target(DonchianBreakout)
    strategy = cls(name="donchian_vt_ref", params=DonchianBreakout.presets["balanced"])
    cost = CostModel.from_configs(ex_cfg.fees, ex_cfg.slippage)

    report_path = write_all_reports(
        store, strategy, data, cost, root / "docs" / "reports", STRATEGY_LABEL
    )
    logger.info("rapport quotidien : %s", report_path)
    print(report_path.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
