# RUNBOOK — exploitation du bot

## Démarrer (paper trading)

```bash
make setup                # une fois
make fetch-data           # historique + rapport qualité
make paper                # boucle planifiée (cycles à chaque clôture de bougie)
# ou en arrière-plan :
nohup .venv/bin/python scripts/run_paper.py --timeframe 1h >> logs/paper_run.out 2>&1 &
```

Démo rapide sans attendre les clôtures : `.venv/bin/python scripts/run_paper.py --cycles 3`.

### Déploiement 24/7 sur VPS (recommandé pour le vrai long-run)

```bash
docker compose up -d --build     # restart: unless-stopped + healthcheck
docker compose logs -f trading-bot
```

## Arrêter

- **Kill switch (recommandé)** : `make kill` — pose `state/KILL`, le bot termine son
  cycle courant, journalise `kill` et devient inerte. Redémarrage : `rm state/KILL`
  puis relancer.
- Docker : `docker compose down` (l'état SQLite et les logs sont dans les volumes).

## Mettre à jour

```bash
make kill && git pull && make setup && make test   # ne redémarrer que si tout est vert
rm state/KILL && make paper
```

## Diagnostiquer un incident

1. `tail -100 logs/trading_bot.log` — chaque cycle logge son action
   (`traded|no_trade|paused|halted|safe_mode|killed`) et l'equity.
2. Journal des décisions (cause exacte de tout arrêt) :
   ```bash
   .venv/bin/python -c "from src.execution.state import StateStore; \
   [print(*d[:3], d[3][:120]) for d in StateStore('state/bot.sqlite').decisions()[-20:]]"
   ```
3. `make report` — rapport quotidien + dashboard `docs/reports/dashboard.html`.

| Symptôme | Cause probable | Action |
|---|---|---|
| `safe_mode` | positions SQLite ≠ broker | NE PAS forcer : examiner `decisions`, corriger la cause, seulement ensuite réaligner l'état |
| `halted` + « perte journalière/drawdown » | circuit breaker R9 | analyser les trades ; le redémarrage réinitialise les fenêtres, à faire consciemment |
| `paused` | pertes consécutives | attendre l'expiration (config `pause_after_losses_minutes`) |
| erreurs fetch répétées | réseau/géo-blocage (Bybit bloque les IP US, cf. ADR-002) | vérifier `data.live_source` dans `config/exchange.yaml` |
| TLS `certificate verify failed` derrière un proxy | bundle CA non lu | exporter `REQUESTS_CA_BUNDLE=<bundle>` — ne JAMAIS désactiver la vérification |

## Restaurer après crash

Rien à faire de spécial : relancer `make paper`. Au démarrage, l'exécuteur recharge
cash + positions depuis `state/bot.sqlite` puis **réconcilie avant toute décision** ;
en cas d'incohérence il part en Safe Mode au lieu de trader. Sauvegarder
régulièrement `state/bot.sqlite` (cron `cp` ou volume snapshot) suffit comme PRA.

## Passer du paper au testnet Bybit (depuis la France)

1. Créer des clés **Demo Trading** Bybit (`api-demo.bybit.com`) ou testnet
   (`testnet.bybit.com`) — jamais les clés du compte réel.
2. `.env` : `EXCHANGE_TESTNET_API_KEY/SECRET`.
3. `config/exchange.yaml` : `mode: testnet`, `data.live_source: bybit`.
4. Le mode `live` reste verrouillé (PermissionError) — cf. GO_LIVE_CHECKLIST.md.
