"""RiskManager : limites dures appliquées côté EXÉCUTEUR (règle R8).

Quelles que soient les demandes des stratégies, ces limites s'appliquent en
dernier. Tout refus/écrêtage est journalisé et retourné à l'appelant pour le
journal des décisions (règle R10 : tout est tracé, y compris les refus).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.utils.config import RiskConfig
from src.utils.logging_setup import get_logger

logger = get_logger("risk.manager")


@dataclass
class ClampReport:
    """Trace des écrêtages appliqués à une matrice de poids cibles."""

    adjustments: list[str] = field(default_factory=list)

    @property
    def was_clamped(self) -> bool:
        return bool(self.adjustments)


class RiskManager:
    """Applique les limites de `risk.yaml` aux poids cibles agrégés."""

    def __init__(self, config: RiskConfig) -> None:
        self.config = config

    def clamp_targets(self, targets: dict[str, float]) -> tuple[dict[str, float], ClampReport]:
        """Écrête les poids cibles par actif puis l'exposition totale.

        Args:
            targets: {symbol: poids demandé ∈ [0, 1]} agrégés des stratégies.

        Returns:
            (poids autorisés, rapport d'écrêtage pour le journal).
        """
        limits = self.config.limits
        report = ClampReport()
        out: dict[str, float] = {}

        for sym, w in targets.items():
            w_clamped = max(0.0, min(w, limits.max_position_pct))
            if w_clamped != w:
                msg = f"{sym}: poids demandé {w:.3f} -> écrêté à {w_clamped:.3f} (max_position_pct)"
                report.adjustments.append(msg)
                logger.warning("REFUS PARTIEL %s", msg)
            out[sym] = w_clamped

        gross = sum(out.values())
        if gross > limits.max_total_exposure_pct and gross > 0:
            scale = limits.max_total_exposure_pct / gross
            for sym in out:
                out[sym] *= scale
            msg = (
                f"exposition brute {gross:.3f} > {limits.max_total_exposure_pct:.3f} "
                f"-> réduction proportionnelle ×{scale:.3f}"
            )
            report.adjustments.append(msg)
            logger.warning("REFUS PARTIEL %s", msg)
        return out, report

    def clamp_order_size(self, symbol: str, order_frac: float) -> tuple[float, str | None]:
        """Plafonne la taille d'UN ordre (fraction du capital). Retourne (taille, refus?)."""
        cap = self.config.limits.max_order_pct
        if abs(order_frac) > cap:
            clamped = cap if order_frac > 0 else -cap
            msg = f"{symbol}: ordre {order_frac:+.3f} écrêté à {clamped:+.3f} (max_order_pct)"
            logger.warning("REFUS PARTIEL %s", msg)
            return clamped, msg
        return order_frac, None

    def leverage_forbidden(self) -> bool:
        return not self.config.limits.leverage_allowed
