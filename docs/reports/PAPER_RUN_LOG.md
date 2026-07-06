# Journal du run de paper trading continu

Objectif mission : fonctionnement continu prouvé par logs horodatés (cible 72 h).
Contrainte d'environnement documentée (ADR-002 addendum, PHASE_7.md) : la session
cloud est éphémère — un watchdog horaire (trigger `paper-trading-watchdog`)
vérifie/relance le bot et consigne ici la durée réellement atteinte. Aucune durée
n'est revendiquée sans preuve.

| Check (UTC) | Bot vivant | Démarré à | Durée continue cumulée | Equity | Décisions journalisées | Note |
|---|---|---|---|---|---|---|
| 2026-07-06 15:39 | ✅ PID 26517 | 2026-07-06 15:39:15 | 0 h (démarrage) | 10 000,00 | 11 | premier cycle OK (no_trade journalisé) |
| 2026-07-06 16:10 | ✅ PID 1930 | 2026-07-06 15:39:15 | ~0,5 h | 10 000,00 | 12 | check watchdog (lecture seule — mode plan actif, mise à jour différée) |
| 2026-07-06 16:29 | 🛑 **ARRÊT DEMANDÉ PAR L'UTILISATEUR** | — | **~0,8 h de run continu prouvé** | 10 000,00 | 12 | kill switch posé à 16:29:28 UTC (`state/KILL`), processus terminé, watchdog horaire supprimé |

## Clôture du run (2026-07-06 19:11 UTC)

- Arrêt à la demande explicite de l'utilisateur (« on arrête le test pour l'instant »).
- Durée de fonctionnement continu prouvée par logs : **≈ 50 minutes** (15:39 → 16:29 UTC) —
  loin de la cible de 72 h de la mission, dit honnêtement. La procédure d'arrêt propre
  (kill switch) et la reprise après crash ont, elles, été démontrées et testées (PHASE_7/9).
- État final : equity 10 000,00 USDT (aucun trade déclenché par la stratégie non validée
  sur la période), 12 décisions journalisées, 0 erreur non gérée.
- Pour relancer plus tard : `rm state/KILL` puis `make paper` (cf. RUNBOOK).
