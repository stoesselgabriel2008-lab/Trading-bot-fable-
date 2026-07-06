# PROGRESS — état final du projet

**Dernière mise à jour :** 2026-07-06 (Phase 10)
**Statut : mission phases 0→10 livrées.** Paper trading en fonctionnement continu
(watchdog horaire actif) — durée accumulée tracée dans `docs/reports/PAPER_RUN_LOG.md`.

## État des phases

| Phase | Intitulé | Statut |
|---|---|---|
| 0 | Initialisation | ✅ (docs/reports/PHASE_0.md) |
| 1 | Recherche web massive | ✅ 52 recherches, 26 lectures intégrales (PHASE_1.md) |
| 2 | Architecture | ✅ (PHASE_2.md) |
| 3 | Pipeline de données | ✅ 9 ans BTC/ETH, corrélations quantifiées (PHASE_3.md) |
| 4 | Moteur de backtest | ✅ 3 tests anti-lookahead + canari, écart réf. 0,84 % (PHASE_4.md) |
| 5 | Stratégies | ✅ 7 familles + overlay + 2 baselines (PHASE_5.md) |
| 6 | Validation anti-illusion | ✅ **0 validée / 38 rejetées** (VALIDATION_REPORT.md, ADR-004) |
| 7 | Exécution / paper trading | ✅ kill switch prouvé, run continu (PHASE_7.md, PAPER_RUN_LOG.md) |
| 8 | Monitoring et rapports | ✅ rapport quotidien, shortfall, dashboard (PHASE_8.md) |
| 9 | Tests, sécurité, qualité | ✅ 128 tests, couverture 91 %, mypy OK, 0 vuln (PHASE_9.md) |
| 10 | Documentation et passation | ✅ README, RUNBOOK, GO_LIVE_CHECKLIST, ce fichier |

## Verdict central (l'essentiel à retenir)

**Aucune des 38 configurations stratégie × actif ne survit au protocole
anti-illusion** — walk-forward OOS à coûts stressés (frais ×1,5, slippage ×2),
sensibilité aux paramètres, Monte Carlo, Deflated Sharpe Ratio avec comptage
honnête (~5 200 configurations), régimes, baseline aléatoire calibrée. L'unique
itération de refonte autorisée (R3 : overlay volatility targeting, pré-enregistré
en Phase 1) a réduit les drawdowns de moitié mais n'a pas créé d'edge : les
meilleures candidates (DonchianBreakout_VT, AtrBreakout_VT — Sharpe ≈ 1,
DD < 20 %) restent indistinguables du hasard (critère C6, P(hasard) ≥ 78 %).

**C'est un succès du protocole** : des rendements OOS jusqu'à +791 % ont été
correctement identifiés comme du beta de marché haussier + sélection, pas de
l'alpha. La valeur livrée est l'infrastructure et l'honnêteté des verdicts.

## Stratégies : validées vs rejetées

- **Validées : 0.**
- **Rejetées : 38** (7 familles × {BTC, ETH, SOL} + momentum portefeuille,
  en versions brute et vol-target). Détail complet par couple avec critères
  échoués, DSR, Monte Carlo et analyse par régime : `docs/VALIDATION_REPORT.md`.
- Baselines opérationnelles : buy & hold, random timing calibré.

## Décisions (docs/adr/)

- **ADR-001** : Python 3.12, ccxt 4.5.64, pandas 2.3.3, backtesting.py en
  contre-vérification — versions vérifiées live sur PyPI.
- **ADR-002** : exchange Bybit (MiCA France + testnet/demo) ; données historiques
  Binance publiques (2017+). Addendum : Bybit géo-bloqué depuis l'IP cloud (US) —
  paper sur données publiques Binance ici, Bybit OK depuis la France.
- **ADR-003** : moteur sur mesure (auditable, anti-lookahead prouvé) plutôt que
  Freqtrade/Nautilus/vectorbt.
- **ADR-004** : périmètre validation 1d ; refonte unique vol-target consommée ;
  paper trading = validation d'infrastructure avec étiquette « NON VALIDÉE ».

## Limites connues (honnêteté de passation)

1. **Bybit géo-bloqué depuis l'environnement cloud** (IP US) : la comparaison
   croisée Binance/Bybit des séries et le testnet Bybit n'ont pas pu être
   exercés d'ici ; à faire depuis la France (RUNBOOK §testnet).
2. **Run continu** : la cible mission de 72 h dépend de la longévité de la
   session cloud ; le watchdog horaire relance et trace la durée RÉELLE dans
   PAPER_RUN_LOG.md — le déploiement VPS docker-compose est la voie pérenne.
3. Validation limitée au timeframe 1d et à 3 actifs (ADR-004) — les données
   1h/4h sont déjà téléchargées pour une extension.
4. Le shortfall paper vs backtest n'a pas encore d'échantillon (0 aller-retour
   paper à ce stade) — le rapport quotidien refuse honnêtement de conclure.
5. Survivorship résiduel : univers BTC/ETH/SOL choisi aujourd'hui ; les résultats
   (déjà tous négatifs) n'en seraient que pires avec des actifs disparus.

## Pistes d'amélioration honnêtes (sans promesse)

- Élargir l'univers à 10-20 cryptos liquides (le momentum cross-sectional n'a
  de sens qu'avec de la largeur) puis re-passer la MÊME batterie.
- Purged/embargoed CV combinatoire en complément du walk-forward.
- Exécution maker (limit orders) pour réduire les coûts — à modéliser d'abord.
- Suivre le shortfall sur plusieurs semaines de paper avant toute conclusion.

## Reprise de session (R13)

Relire ce fichier, `docs/ARCHITECTURE.md`, le dernier rapport de phase et
`docs/reports/PAPER_RUN_LOG.md`. Bot : `pgrep -f run_paper.py` ; relance :
`REQUESTS_CA_BUNDLE=/root/.ccr/ca-bundle.crt nohup .venv/bin/python scripts/run_paper.py --timeframe 1h >> logs/paper_run.out 2>&1 &`
