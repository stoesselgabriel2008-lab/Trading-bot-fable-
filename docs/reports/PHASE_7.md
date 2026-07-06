# Rapport de Phase 7 — Exécution et automatisation (paper)

**Date :** 2026-07-06 · **Statut : ✅ infrastructure livrée et démontrée ; run continu en cours d'accumulation**

## Livré

- `src/risk/manager.py` : limites R8 côté exécuteur (position max, exposition max,
  taille d'ordre max), refus journalisés ; levier interdit.
- `src/risk/breakers.py` : circuit breakers R9 (pertes consécutives → pause ;
  perte horaire/journalière, drawdown, taux d'erreurs API → HALT ; divergence de
  réconciliation → HALT).
- `src/execution/state.py` : SQLite WAL (positions, ordres avec clientOrderId,
  equity, décisions, kv), écritures idempotentes, `reconcile()` 3 vérités.
- `src/execution/broker.py` : `PaperBroker` (fills locaux + slippage + frais,
  interdit découvert/dépassement de cash) ; `CcxtBroker` (retries backoff 2/4/8/16 s,
  clientOrderId idempotents, sandbox testnet ; **mode live verrouillé — lève
  PermissionError, R6**).
- `src/execution/executor.py` : cycle en 8 étapes (kill switch → données clôturées →
  réconciliation → breakers → stratégie → clamp R8 → ordres delta → persistance),
  reprise après crash (rechargement SQLite au démarrage).
- `src/execution/scheduler.py` : APScheduler aligné sur les clôtures UTC (+20 s de
  grâce) ; mode fast-cycles pour tests.
- `scripts/run_paper.py` (= make paper), `scripts/kill.py` (= make kill).
- `Dockerfile` + `docker-compose.yml` (restart: unless-stopped + healthcheck sur la
  fraîcheur des logs) pour un déploiement VPS 24/7 (RUNBOOK).

## Preuves d'exécution (sorties réelles, R1)

### Cycles paper sur données LIVE (Binance public — ADR-002 addendum)
```
=== PAPER TRADING START — DonchianBreakout_VT[balanced] — STRATÉGIE NON VALIDÉE
    (VALIDATION_REPORT.md) — observation d'infrastructure uniquement ===
cycle 2026-07-06T15:38:28 : no_trade (equity=10000.00)
```
Journal des décisions (SQLite) — chaque cycle trace `target` puis `order`/`no_trade` :
```
2026-07-06T15:38:32 target - {"strategy": "DonchianBreakout_VT[balanced] — STRATÉGIE NON VALIDÉE...
2026-07-06T15:38:32 no_trade - {"reason": "poids dans la tolérance"}
```

### Kill switch déclenché volontairement puis reprise propre
```
15:38:55 CRITICAL KILL SWITCH posé : state/KILL — le bot s'arrêtera au prochain cycle
15:38:56 CRITICAL KILL SWITCH détecté -> arrêt propre
15:38:56 cycle : killed (equity=10000.00) kill switch
--- flag retiré, redémarrage:
15:39:00 cycle : no_trade (equity=10000.00)     <- reprise avec rechargement d'état
```

### Robustesse face aux erreurs API (constatée en conditions réelles)
Avant la bascule de source (Bybit géo-bloqué depuis l'IP cloud), le bot a encaissé
3 cycles d'erreurs 403 SANS crash : erreurs comptées par le breaker, décisions
`error` journalisées, cycle suivant retenté — comportement exactement voulu.

### Tests unitaires
```
106 passed  (dont 15 nouveaux : clamp R8, breakers R9, réconciliation,
             idempotence clientOrderId, PaperBroker frais/slippage/découvert)
```

## Critère « 72 h de paper trading continu » — statut honnête

Le bot tourne en arrière-plan (cycles horaires) depuis 2026-07-06 15:39 UTC, avec
un watchdog horaire (trigger) qui vérifie/relance et consigne la durée réelle dans
`docs/reports/PAPER_RUN_LOG.md`. **La durée atteinte sera celle prouvée par les
logs — aucune revendication au-delà.** L'environnement de session étant éphémère,
le RUNBOOK documente le déploiement docker-compose pour un vrai 24/7 sur VPS
(restart automatique + healthcheck).

## Rappel honnêteté

La stratégie exécutée est étiquetée dans les logs, la config et les rapports :
**« NON VALIDÉE — observation d'infrastructure uniquement »** (ADR-004). Le mode
live reste verrouillé et lèverait une PermissionError même avec `live_trading: true`.
