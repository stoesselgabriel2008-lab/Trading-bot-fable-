# PROGRESS — état courant du projet

**Dernière mise à jour :** 2026-07-06
**Phase en cours :** Phase 2 — Architecture

## État des phases

| Phase | Intitulé | Statut |
|---|---|---|
| 0 | Initialisation | ✅ (docs/reports/PHASE_0.md) |
| 1 | Recherche web massive | ✅ (52 recherches, 26 lectures — docs/reports/PHASE_1.md) |
| 2 | Architecture | 🔄 en cours |
| 3 | Pipeline de données | ⬜ |
| 4 | Moteur de backtest | ⬜ |
| 5 | Stratégies | ⬜ |
| 6 | Validation anti-illusion | ⬜ |
| 7 | Exécution / paper trading | ⬜ |
| 8 | Monitoring et rapports | ⬜ |
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

- [ ] Phase 2 : ARCHITECTURE.md + squelettes de modules + tests d'import

## Notes de reprise (R13)

En cas de reprise de session : relire ce fichier, `docs/ARCHITECTURE.md`
et le dernier rapport dans `docs/reports/` avant d'écrire du code.
