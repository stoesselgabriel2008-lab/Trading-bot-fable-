# PROGRESS — état courant du projet

**Dernière mise à jour :** 2026-07-06
**Phase en cours :** Phase 8 — Monitoring et rapports

## État des phases

| Phase | Intitulé | Statut |
|---|---|---|
| 0 | Initialisation | ✅ (docs/reports/PHASE_0.md) |
| 1 | Recherche web massive | ✅ (52 recherches, 26 lectures — docs/reports/PHASE_1.md) |
| 2 | Architecture | ✅ (docs/reports/PHASE_2.md) |
| 3 | Pipeline de données | ✅ (9 ans BTC/ETH, corrélations quantifiées — PHASE_3.md) |
| 4 | Moteur de backtest | ✅ (3 tests anti-lookahead + canari, écart réf. 0,84 % — PHASE_4.md) |
| 5 | Stratégies | ✅ (7 familles + overlay + 2 baselines — PHASE_5.md) |
| 6 | Validation anti-illusion | ✅ **0 validée / 38 rejetées** (VALIDATION_REPORT.md, ADR-004) |
| 7 | Exécution / paper trading | ✅ (kill switch prouvé, run continu en accumulation — PHASE_7.md, PAPER_RUN_LOG.md) |
| 8 | Monitoring et rapports | 🔄 en cours |
| 9 | Tests, sécurité, qualité | ⬜ |
| 10 | Documentation et passation | ⬜ |

## Décisions prises (résumé — détail dans docs/adr/)

- **ADR-001 (stack)** : Python 3.12, pandas 2.3.3 (pas 3.0.x, trop récent pour
  l'écosystème), ccxt 4.5.64, backtesting.py comme moteur de référence pour la
  validation croisée. Versions vérifiées en direct sur PyPI le 2026-07-06.
- **ADR-002 (exchange)** : Bybit (MiCA France + testnet & demo mainnet) ; données
  historiques via API publique Binance. ⚠️ Binance a quitté l'UE le 01/07/2026.
- **ADR-003 (framework)** : sur mesure + ccxt ; backtesting.py en contre-vérification.

## TODO immédiat

- [ ] Phase 8 : rapport quotidien, shortfall backtest vs paper, dashboard HTML, alertes webhook

## Verdict central du projet (Phase 6)

**Aucune des 38 configurations stratégie × actif ne survit au protocole
anti-illusion** (même après l'unique refonte vol-target autorisée par R3).
Meilleures candidates rejetées : DonchianBreakout_VT et AtrBreakout_VT
(Sharpe ≈ 1, DD < 20 %) — mais indistinguables d'une baseline aléatoire (C6)
et P(hasard) ≥ 78 %. Le paper trading sert donc à valider l'infrastructure,
avec étiquette explicite « stratégie NON validée — observation uniquement ».

## Limites connues (à ce stade)

- Bybit géo-bloqué depuis l'environnement cloud (IP US) : paper trading sur données
  publiques Binance ici ; Bybit EU OK depuis la France (cf. ADR-002 addendum).
- Corrélation BTC-ETH mesurée à 0,805 : diversification multi-actifs partiellement
  illusoire — pris en compte via la limite d'exposition totale.

## Notes de reprise (R13)

En cas de reprise de session : relire ce fichier, `docs/ARCHITECTURE.md`
et le dernier rapport dans `docs/reports/` avant d'écrire du code.
