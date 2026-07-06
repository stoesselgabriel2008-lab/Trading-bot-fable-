# Trading Bot — système crypto multi-actifs, multi-stratégies

Système de trading algorithmique crypto avec pipeline de données, moteur de backtest
réaliste, **batterie de validation anti-illusion**, exécution automatique en
**paper trading** (par défaut), gestion du risque codée en dur, monitoring et tests.

> ⚠️ **Avertissement** : ce projet ne promet aucun profit. Le trading de
> cryptomonnaies peut entraîner la perte totale du capital engagé. Le mode
> live est verrouillé par défaut (`live_trading: false`) et hors du périmètre
> de ce dépôt — voir `docs/GO_LIVE_CHECKLIST.md`.

## Installation (5 commandes)

```bash
git clone <ce-dépôt> && cd Trading-bot-fable-
make setup            # venv + dépendances pinnées
cp .env.example .env  # secrets optionnels (inutile en mode paper)
make test             # suite de tests
make fetch-data       # historique OHLCV (Phase 3+)
```

## Démarrage du paper trading (1 commande)

```bash
make paper
```

## Documentation

| Fichier | Contenu |
|---|---|
| `PROGRESS.md` | État courant du projet, phase en cours |
| `docs/RESEARCH.md` | Recherches web sourcées et datées |
| `docs/ARCHITECTURE.md` | Architecture et choix techniques |
| `docs/VALIDATION_REPORT.md` | Verdicts honnêtes par stratégie |
| `docs/RUNBOOK.md` | Exploitation : démarrer / arrêter / incidents |
| `docs/GO_LIVE_CHECKLIST.md` | Conditions strictes avant tout live (non activé) |
| `docs/adr/` | Décisions d'architecture |
| `docs/reports/` | Rapports de phase et rapports quotidiens |
