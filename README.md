# Trading Bot — système crypto multi-actifs, multi-stratégies, validé honnêtement

Système de trading algorithmique crypto complet : pipeline de données (9 ans
d'OHLCV), moteur de backtest réaliste prouvé anti-lookahead, **batterie de
validation anti-illusion** (walk-forward, Monte Carlo, Deflated Sharpe Ratio,
stress des coûts), exécution automatique en **paper trading**, limites de risque
codées en dur, circuit breakers, kill switch, monitoring et 128 tests (91 % de
couverture).

> 🔍 **Le résultat central de ce projet est un verdict honnête** : sur 38
> configurations stratégie × actif testées, **0 a survécu** au protocole de
> validation ([docs/VALIDATION_REPORT.md](docs/VALIDATION_REPORT.md)). Des
> rendements out-of-sample spectaculaires (+791 %) se sont révélés
> indistinguables d'une baseline aléatoire dans un marché haussier. C'est
> exactement l'illusion que cette infrastructure est conçue pour détecter.

> ⚠️ **Avertissement** : aucun profit n'est promis ni possible à promettre. Le
> trading de cryptomonnaies peut entraîner la perte totale du capital. Le mode
> live est doublement verrouillé (config + PermissionError dans le code) et
> aucune stratégie n'y serait éligible — voir `docs/GO_LIVE_CHECKLIST.md`.

## Installation (5 commandes)

```bash
git clone <ce-dépôt> && cd Trading-bot-fable-
make setup            # venv + dépendances pinnées (vérifiées sur PyPI)
cp .env.example .env  # secrets optionnels (inutile en mode paper)
make test             # 128 tests
make fetch-data       # ~9 ans d'OHLCV BTC/ETH/SOL + rapport qualité
```

## Démarrage du paper trading (1 commande)

```bash
make paper            # cycles à chaque clôture de bougie ; make kill pour arrêter
```

La stratégie exécutée est étiquetée « NON VALIDÉE — observation d'infrastructure
uniquement » dans chaque log et rapport.

## Commandes

| Commande | Effet |
|---|---|
| `make backtest` / `make validate` | backtests + batterie anti-illusion complète |
| `make report` | rapport quotidien + dashboard HTML + exports CSV |
| `make kill` | kill switch (arrêt propre au cycle suivant) |
| `make lint` / `make typecheck` / `make audit` | ruff · mypy · pip-audit |
| `docker compose up -d` | déploiement 24/7 (restart auto + healthcheck) |

## Documentation

| Fichier | Contenu |
|---|---|
| [PROGRESS.md](PROGRESS.md) | État final, décisions, limites connues |
| [docs/VALIDATION_REPORT.md](docs/VALIDATION_REPORT.md) | **Verdicts détaillés des 38 configurations** |
| [docs/RESEARCH.md](docs/RESEARCH.md) | 52 recherches web sourcées et datées |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Architecture et contrats d'interface |
| [docs/RUNBOOK.md](docs/RUNBOOK.md) | Démarrer / arrêter / incidents / restauration |
| [docs/GO_LIVE_CHECKLIST.md](docs/GO_LIVE_CHECKLIST.md) | Conditions strictes avant tout live (non activé) |
| [docs/adr/](docs/adr/) | 4 décisions d'architecture motivées |
| [docs/reports/](docs/reports/) | Rapports de phase 0→10 + rapports quotidiens |
