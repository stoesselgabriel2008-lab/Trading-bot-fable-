"""KILL SWITCH manuel (usage : make kill).

Pose le flag ``state/KILL`` : l'exécuteur s'arrête proprement au cycle suivant
(journalisation, aucune nouvelle position). Pour redémarrer : supprimer le flag
(``rm state/KILL``) puis relancer ``make paper`` — la reprise recharge l'état
SQLite et réconcilie avant toute décision.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.utils.logging_setup import setup_logging

KILL_FLAG = Path(__file__).resolve().parents[1] / "state" / "KILL"


def main() -> int:
    logger = setup_logging()
    KILL_FLAG.parent.mkdir(parents=True, exist_ok=True)
    KILL_FLAG.write_text(f"kill demandé à {datetime.now(UTC).isoformat()}\n", encoding="utf-8")
    logger.critical("KILL SWITCH posé : %s — le bot s'arrêtera au prochain cycle", KILL_FLAG)
    print(f"Kill switch posé ({KILL_FLAG}). Le bot s'arrête proprement au prochain cycle.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
