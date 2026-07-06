# RESEARCH — Synthèse des recherches web (Phase 1)

**Consultations effectuées le 2026-07-06.** Chaque affirmation clé est recoupée par
au moins 2 sources (règle R4). Les conclusions « pour CE projet » figurent en fin de
chaque section. Compteur en fin de fichier.

---

## 1. Frameworks open-source existants

### Constats (sources datées du 2026-07-06)

| Framework | Nature | Licence | Maturité / communauté | Limites connues |
|---|---|---|---|---|
| **Freqtrade** | Bot directionnel complet (OHLCV) | GPL-3.0 | ~49k ⭐, releases mensuelles, actif depuis 2017 | Pas de market making/arbitrage ; bougies seulement (pas de tick/carnet) ; GPL contraignante |
| **Hummingbot** | Market making / liquidité | Apache 2.0 | ~6k ⭐, v2.13 (2026) | Backtesting basique (pas de walk-forward ni d'hyperopt) ; orienté carnet d'ordres |
| **Jesse** | Recherche + backtest | MIT (cœur) | ~5k ⭐ | Moins d'intégrations live ; écosystème plus petit |
| **OctoBot** | Bot « clé en main » | GPL-3.0 | ~5,4k ⭐, v2.1.1 (03/2026) | Orienté grand public ; personnalisation profonde plus difficile |
| **Nautilus Trader** | Plateforme événementielle production-grade (cœur Rust) | LGPL | Très actif | Courbe d'apprentissage élevée ; complexité disproportionnée pour ce projet |
| **vectorbt** | Backtest vectorisé (recherche) | Version libre en maintenance seule ; features → PRO payant | populaire | Pas d'exécution live ; numba/deps sensibles |
| **backtesting.py** | Backtest simple (recherche) | AGPL-3.0* | 0.6.5 (2026, à nouveau maintenu) | Pas de live ; portefeuille mono-actif par backtest |
| **backtrader** | Backtest event-driven | GPL-3.0 | Développement arrêté ~2018 | Non maintenu — écarté |
| **ccxt** | Connectivité unifiée 100+ exchanges | **MIT** | ~42k ⭐, 97k+ commits, très actif ; ~105 exchanges dont ~24 « certifiés » | Rate limiter intégré « expérimental » à ajuster soi-même |

Sources principales :
- https://github.com/freqtrade/freqtrade et https://www.freqtrade.io/en/stable/ (lu intégralement 2026-07-06) — Python 3.11+, dry-run, disclaimer « educational purposes only ».
- https://trendrider.net/blog/freqtrade-vs-hummingbot-vs-ccxt-2026 ; https://alexbobes.com/crypto/best-freqtrade-alternatives/ (comparatifs 2026).
- https://github.com/ccxt/ccxt (lu intégralement 2026-07-06) — licence MIT, ~105 exchanges, rate limiting intégré, sandbox par exchange.
- https://nautilustrader.io/ ; https://github.com/nautechsystems/nautilus_trader.
- https://greyhoundanalytics.com/blog/vectorbt-vs-backtrader/ ; https://pineify.app/resources/blog/best-python-backtesting-library-the-complete-guide-for-algorithmic-traders (vectorbt libre non développé activement ; backtrader arrêté ~2018).
- https://github.com/Drakkar-Software/OctoBot ; https://coincodecap.com/open-source-trading-bots-on-github.

### Points de désaccord entre sources
- Le nombre d'étoiles GitHub de Freqtrade varie selon les articles (25k à 49k) — les comparatifs recyclent des chiffres anciens ; foi donnée au dépôt GitHub lui-même.
- Certains articles présentent le backtest de Jesse comme « le plus honnête » — invérifiable ; tous les moteurs exigent nos propres tests anti-lookahead de toute façon.

### Conclusion pour CE projet (→ ADR-003)
**Construire sur mesure autour de ccxt (MIT).** Justification : (a) contrôle total de la
modélisation des coûts et du protocole de validation — cœur de la mission ; (b) éviter la
GPL de Freqtrade et son couplage fort ; (c) backtesting.py sert uniquement de moteur de
référence pour la validation croisée (Phase 4) ; (d) Nautilus surdimensionné.
Briques réutilisées : **ccxt** (connectivité + testnets), **backtesting.py** (contre-vérification),
pandas/pyarrow (données).

---

## 2. Exchanges et APIs

### Fait majeur découvert (impacte tout le projet)
**Binance a cessé de servir l'UE — dont la France — au 1er juillet 2026**, faute de licence
MiCA (demande retirée en Grèce, re-dépôt annoncé en France). Depuis le 01/07/2026 : plus de
nouveaux ordres spot, dépôts ni inscriptions pour les clients UE ; retraits ouverts.
Sources concordantes (≥2, R4) :
- https://www.coindesk.com/policy/2026/06/26/binance-tells-eu-users-it-will-no-longer-provide-services-after-failing-to-secure-mica-license (2026-06-26)
- https://www.euronews.com/business/2026/06/25/binance-to-halt-crypto-services-across-eu-countries-after-failing-to-secure-mica-approval (2026-06-25)

### Licences MiCA (situation au 2026-07-06)
| Exchange | Licence MiCA | Entité / pays / date |
|---|---|---|
| **Bybit** | ✅ | Bybit EU GmbH, FMA Autriche, 28/05/2025 — sert 29 pays EU/EEE **dont la France** ; l'exchange *global* Bybit restreint les résidents EEE à partir du 01/07/2026 (migration vers Bybit EU) ; **pas de futures pour l'UE** (MiFID requis), marge ≤ 10x |
| **OKX** | ✅ | OKX Europe Ltd, MFSA Malte, 27/01/2025 |
| **Kraken** | ✅ | Payward Europe Solutions, Banque centrale d'Irlande, 25/06/2025 |
| **Coinbase** | ✅ | CSSF Luxembourg, 20/06/2025 |
| **Binance** | ❌ | Exclu de l'UE au 01/07/2026 |

Sources : https://casptracker.eu/exchange/bybit/ (lu intégralement, « last verified 6 July 2026 ») ;
https://www.fintechweekly.com/magazine/articles/bybit-micar-license-austria-european-headquarters ;
https://paybis.com/blog/mica-licensed-crypto-exchanges/ ; https://www.coingabbar.com/en/crypto-currency-news/binance-eu-mica-license-withdrawal-july-2026-coinbase-kraken.

### Environnements de test (critère n°1 du choix)
| Exchange | Testnet/démo | Qualité |
|---|---|---|
| **Binance** | Spot testnet https://testnet.binance.vision (login GitHub, clés gratuites, fonds virtuels, mêmes limites que la prod, clés conservées lors des resets) | Excellent techniquement, mais exchange inutilisable légalement en France pour du réel |
| **Bybit** | **Deux** environnements : testnet complet (testnet.bybit.com) + **Demo Trading sur mainnet** (api-demo.bybit.com, données de marché réelles, compte UTA spot+dérivés) | Excellent — le demo mainnet est idéal : données réelles, exécution simulée |
| **OKX** | Demo trading via header `x-simulated-trading: 1` + clés API démo dédiées | Bon |
| **Kraken** | Démo **futures uniquement** (demo-futures.kraken.com) ; spot : seulement `validate=true` sur les ordres | Insuffisant pour le spot |
| **Coinbase** | Sandbox Advanced Trade : réponses **mockées** (Accounts/Orders seulement) | Faible |

Sources : https://developers.binance.com/docs/binance-spot-api-docs/testnet/general-info ;
https://testnet.binance.vision/ ; https://bybit-exchange.github.io/docs/v5/demo ;
https://www.bybit.com/en/help-center/article/FAQ-Demo-Trading ; https://www.okx.com/docs-v5/en/ ;
https://support.kraken.com/hc/en-us/articles/360026192132 ; https://docs.cdp.coinbase.com/coinbase-app/advanced-trade-apis/sandbox.

### Frais spot réels (tier de base, recoupés 2 sources chacun)
| Exchange | Maker | Taker | Sources |
|---|---|---|---|
| Binance | 0,10 % | 0,10 % | binance.com/en/fee/spotMaker ; bitdegree.org/crypto/tutorials/binance-fees |
| **Bybit** | **0,10 %** | **0,10 %** | bybit.com/en/help-center/article/Trading-Fee-Structure ; cointribune.com/en/bybit-fees-complete-2026-pricing-guide |
| OKX (tier base) | ~0,08 % | ~0,10 % | okx.com (barème) ; comparatifs 2026 — à re-vérifier si OKX devient l'exchange principal |

→ **Hypothèse de coût du backtest : 0,10 % taker** (+ slippage), stress ×1,5 en Phase 6.

### Données kline
- **Binance** : endpoint public `data-api.binance.vision /api/v3/klines` **sans authentification**,
  historique depuis ~2017 (BTC/USDT spot), 1000 bougies/requête + dumps bulk
  https://data.binance.vision. Sources : developers.binance.com/docs/binance-spot-api-docs/faqs/market_data_only ;
  github.com/binance/binance-public-data.
- **Bybit** : `/v5/market/kline`, max 1000 bougies/requête, spot+linear+inverse
  (doc lue intégralement) ; profondeur d'historique spot non documentée → **à mesurer
  empiriquement en Phase 3**. Source : bybit-exchange.github.io/docs/v5/market/kline.

### Conclusion pour CE projet (→ ADR-002)
- **Exchange principal : Bybit** — seul à cumuler licence MiCA valable en France,
  testnet complet ET demo trading sur données mainnet, bon support ccxt (certifié).
- **Source de données de backtest : API publique Binance** (sans compte ni clé, historique
  le plus profond depuis 2017, licite pour de la donnée publique), complétée par Bybit
  pour vérifier la cohérence des séries. Le paper trading local consomme les données
  live Bybit publiques.
- Kraken/Coinbase écartés (testnet spot insuffisant). OKX = alternative de secours.

---

## 3. Familles de stratégies — état de l'art

| Famille | Logique | Conditions favorables | Conditions défavorables | Pièges connus |
|---|---|---|---|---|
| **Trend following (EMA cross, MACD)** | Suivre la direction | Marchés directionnels | Ranges (~60 % du temps en crypto → whipsaws) | Lag structurel ; « une partie du mouvement est déjà passée » ; faibles perfs intraday BTC documentées |
| **Canaux de Donchian (Turtle)** | Breakout de plus hauts/bas N jours | Tendances longues | Marchés hachés | L'edge original (années 80) s'est érodé après publication des règles ; les sorties breakout marchent moins bien qu'avant |
| **Mean reversion (RSI, Bollinger, z-score)** | Retour à la moyenne | Ranges calmes | **Tendances fortes : « RSI peut rester extrême », shorter un bull run parabolique est fatal** | Nécessite time-stop ; altcoins fins ignorent la réversion |
| **Breakout de volatilité (ATR)** | Compression → expansion | Après consolidation | Faux breakouts en basse volatilité | Exiger un mouvement > 1×ATR pour filtrer ; ATR ne prédit pas la direction |
| **Momentum / rotation multi-actifs** | Time-series (px vs MM200) ou cross-sectional (BTC vs ETH vs SOL) | Bull markets larges | **Crashs de momentum documentés académiquement** (Springer 2025) | Gestion par volatility management recommandée par la littérature |
| **Grid trading** | Achats/ventes en grille dans un range | Range latéral | **Breakout hors grille : « un seul breakout peut effacer des mois de gains »** ; bear = accumulation d'un actif qui chute | Stop-loss global obligatoire |
| **DCA conditionnel** | Achats périodiques conditionnés (ex. Fear & Greed) | Long terme, marchés baissiers pour accumuler | Bear prolongé sans rebond | Chiffres marketing (« 6 712 % ») = périodes cerise ; passer par NOTRE validation |
| **Carry funding rate (perp)** | Long spot + short perp, collecter le funding | Funding positif élevé | Retournement du funding, crash (liquidation de la jambe perp) | ~19 % annualisé à 0,015 %/8h d'après sources ; compression du funding par la concurrence ; BIS WP n°1087 documente le crash risk. **Bybit EU n'offre pas les futures aux particuliers UE (MiFID)** → famille documentée mais non implémentable en réel pour un résident FR sur Bybit EU |
| **Volatility targeting (overlay)** | Cibler une volatilité constante | Améliore le Sharpe des « risk assets » (recherche Man Group / Alpha Architect) | Rebalancing coûteux ; réductions rapides ratent les rebonds | Ce n'est pas une stratégie autonome mais un overlay de sizing |

Sources : pruviq.com/blog/ema-crossover-strategy-guide ; arxiv.org/pdf/2009.12155 (lu, PDF —
« 255 % walkforward annualised returns » sur 2010-2020 : période exceptionnellement haussière,
à considérer avec un scepticisme maximal) ; lizardindicators.com/donchian-channel-strategy ;
trendspider.com/learning-center/mean-reversion-trading-strategies ; blog.traderspost.io/article/atr-trading-strategies-guide ;
link.springer.com/article/10.1007/s11408-025-00474-9 ; bitsgap.com/blog/grid-trading-strategy-explained ;
coinbase.com/learn/advanced-trading/what-is-a-grid-trading-bot ; spotedcrypto.com (DCA, chiffres promotionnels) ;
bis.org/publ/work1087.pdf (lu, PDF) ; coinglass.com/learn/what-is-funding-rate-arbitrage (lu) ;
quantpedia.com/an-introduction-to-volatility-targeting (lu) ; man.com/insights/the-impact-of-volatility-targeting.

### Conclusion pour CE projet
Implémenter en Phase 5 : (1) EMA cross + filtre de tendance, (2) Donchian breakout,
(3) mean reversion RSI/Bollinger avec time-stop, (4) breakout ATR, (5) momentum
cross-sectional BTC/ETH/SOL, (6) DCA conditionnel, (7) grid borné avec stop global,
(8) overlay volatility targeting applicable aux stratégies 1-5. Le carry funding est
documenté mais exclu de l'implémentation (non accessible UE + périmètre spot).

---

## 4. Pièges du backtest — LE sujet central

| Piège | Définition | Protection concrète DANS ce projet |
|---|---|---|
| **Lookahead bias** | De l'info future fuit dans la décision (« un décalage d'un pas suffit à invalider tout le backtest ») | Signal calculé sur bougie t → exécution à l'open t+1 ; test unitaire de décalage ; **test random-walk** (toute stratégie doit rendre ≈0 avant frais sur du bruit) ; validation croisée avec backtesting.py |
| **Survivorship bias** | Ne tester que les survivants (LUNA, FTT… ont disparu) ; inflation documentée de 200-400 % des rendements | Univers fixe BTC/ETH/SOL déclaré à l'avance (grosses capitalisations à longue histoire), pas de sélection rétrospective d'altcoins gagnants ; biais résiduel documenté honnêtement dans le VALIDATION_REPORT |
| **Overfitting / data snooping** | « Plus on teste de stratégies, plus on trouve un faux positif » (50 tests à 5 % → ~2,5 faux positifs) | Comptage exhaustif de TOUTES les configurations testées ; Deflated Sharpe Ratio ; une seule itération de refonte par stratégie (R3) |
| **Tests multiples** | Sélectionner le max de N essais gonfle le Sharpe | **DSR (Bailey & López de Prado)** : DSR = Φ((SR̂−SR₀)·√(T−1) / √(1−γ̂₃·SR₀+((γ̂₄−1)/4)·SR₀²)) avec SR₀ = √V[SR̂ₙ]·((1−γ)Φ⁻¹(1−1/N)+γΦ⁻¹(1−1/(Ne))) — formule complète vérifiée sur Wikipedia + papier original (davidhbailey.com, lu) |
| **Walk-forward mal fait** | Fenêtres trop courtes = paramètres instables ; trop longues = régimes obsolètes | Rolling WF, ratio IS/OOS ≈ 80/20, agrégation de TOUTES les fenêtres OOS, ≥ 60 % de fenêtres positives exigées |
| **Purged/embargoed CV** | Le K-fold standard fuit par chevauchement temporel des labels | Purge des observations chevauchantes + embargo après chaque fold de test (approche López de Prado) pour toute CV utilisée |
| **Coûts irréalistes** | « Les frais réels diffèrent des frais documentés (0,04 % vs 0,50 % observé) » | Frais taker 0,10 % (vérifiés 2 sources) + slippage 5 bps de base pour BTC/ETH (fourchette réaliste 0,05-0,1 % top-10) ; stress frais ×1,5 et slippage ×2 en Phase 6 ; cap de participation au volume |
| **Bougies incomplètes** | La dernière bougie OHLCV est incomplète tant qu'elle n'est pas clôturée | N'agir qu'après confirmation de clôture ; le pipeline rejette la bougie courante |

Sources : quantjourney.substack.com/p/advanced-look-ahead-bias-prevention ; mikeharrisny.medium.com ;
robuxio.com/algorithmic-crypto-trading-x-trading-biases (lu — 7 biais) ; stratbase.ai/en/blog/survivorship-bias-crypto ;
en.wikipedia.org/wiki/Deflated_Sharpe_ratio (lu — formule) ; davidhbailey.com/dhbpapers/deflated-sharpe.pdf (lu) ;
papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551 ; blog.quantinsti.com/walk-forward-optimization-introduction (lu) ;
blog.quantinsti.com/cross-validation-embargo-purging-combinatorial (lu) ; sciencedirect.com/science/article/abs/pii/S0950705124011110 ;
florinelchis.medium.com (lu — frais réels vs documentés) ; paybis.com/blog/how-to-backtest-crypto-bot (lu — slippage par tiers de liquidité) ;
luxalgo.com/blog/backtesting-limitations-slippage-and-liquidity-explained (lu — fourchettes crypto 0,1-0,5 % normal, 1-5 % stress).

### Monte Carlo (Phase 6)
Bootstrap des trades avec remise (≥ 1000 tirages, 5000 idéal pour les percentiles de
drawdown) → distributions de rendement/drawdown, IC 95 %, percentile 95 du max DD comme
pire cas de planification. Source : quantproof.io/blog/monte-carlo-simulations-trading-strategy-validation ;
buildalpha.com/monte-carlo-simulation.

### Baseline aléatoire (Phase 5)
Stratégie à switchs aléatoires calibrée sur le turnover réel : P(switch) = 1/D où D =
durée moyenne de position de la stratégie comparée ; ~1000 tirages Monte Carlo pour situer
la stratégie dans la distribution du hasard. ≥ 100 trades minimum pour la significativité
(200-500 souhaités). Sources : arxiv.org/pdf/2602.00133 ; tradezella.com/blog/backtesting-trading-strategies.

---

## 5. Risk management

- **Fixed fractional** : risquer un % fixe du capital par trade — simple, conservateur. Kelly
  optimal en théorie mais variance intolérable → **Kelly fractionné (25-50 % du Kelly)** si utilisé.
  Sources : quantifiedstrategies.com/position-sizing-strategies ; medium (Kelly vs FF).
- **Stops ATR** : stop = entrée ± k×ATR (k≈2 swing, jusqu'à 3-4 en forte vol) ;
  **sizing par volatilité** : taille = risque_$_par_trade / (k×ATR) — la vol élevée réduit
  mécaniquement la taille. Sources : luxalgo.com/blog/average-true-range-dynamic-stop-loss-levels ;
  mudrex.com/learn/average-true-range-crypto.
- **Corrélations crypto** : ETH/BNB/LTC corrélés à BTC entre **0,70 et 0,90** (CME Group,
  finst.com) → « posséder 10 cryptos ≠ diversification ». **Quantification prévue en Phase 3**
  sur nos données (matrice de corrélation des rendements journaliers BTC/ETH/SOL, publiée
  dans le rapport de qualité). Conséquence : plafond d'exposition TOTALE (0,60) bien plus
  contraignant que la somme des plafonds par actif.
- **Circuit breakers** (valeurs usuelles des sources : arrêt journalier à −3 %, hebdo −7 %,
  mensuel −15 % ; pause après N pertes consécutives ; nos valeurs dans `risk.yaml`) :
  cripton.ai/en/guides/bot-risk-management ; darkbot.io (règle 1-2 %).

---

## 6. Données

- OHLCV via ccxt `fetch_ohlcv` : pagination time-based (`since`/`until`, flag `paginate`),
  **bougies intermédiaires parfois manquantes selon l'exchange, dernière bougie incomplète**
  → contrôles obligatoires. Sources : github.com/ccxt/ccxt/wiki/manual ; issues #12341, #12855.
- Granularités : 1h/4h/1d retenues. Historique : Binance spot depuis ~2017 (public, sans clé,
  `data-api.binance.vision`) ; SOL/USDT depuis ~2020 (listing). Bybit : profondeur à mesurer.
- **Contrôles qualité** (dev.to data quality, lu ; coinapi.io) : gaps (> 1,5× l'intervalle),
  doublons (dédoublonnage par timestamp), bougies aberrantes (|close-to-close| > 5 %,
  range > 10 % → à examiner, winsorisation éventuelle documentée), volume nul, timestamps
  non alignés (tout en UTC), cohérence high ≥ max(open,close) ≥ min(open,close) ≥ low.
  **Politique du projet : jamais d'interpolation silencieuse** — les gaps sont journalisés
  et conservés ; forward-fill uniquement pour l'affichage, jamais pour les signaux.
- Spot vs perp : prix liés par le funding (payé ~toutes les 8 h) ; nos backtests = **spot
  uniquement** (cohérent avec Bybit EU sans futures). Sources : wikipedia.org/wiki/Perpetual_futures (lu) ;
  coinapi.io/blog/crypto-futures-explained.

---

## 7. Robustesse opérationnelle

- **Idempotence des ordres** : clientOrderId unique (UUID) par intention d'ordre ; en cas de
  timeout réseau, re-soumettre avec le MÊME id → l'exchange dédoublonne. Stockage local
  des ids et statuts. Sources : medium/idempotency articles ; hackernoon.com/how-to-fix-duplicate-api-requests.
- **Réconciliation d'état** (mql5.com/en/articles/22615, lu) : comparer à chaque démarrage ET
  périodiquement (1) position exchange, (2) état mémoire, (3) enregistrement SQLite. Toute
  divergence → **Safe Mode** : suspension de l'automatisation, alerte, pas de « réparation »
  automatique silencieuse.
- **15 failure patterns** (florinelchis, lu) — les plus pertinents : frais réels ≠ documentés ;
  écritures fichier non atomiques (→ écrire via fichier temporaire + rename atomique) ;
  positions fantômes en base ; cooldown qui ne compte que les succès ; ordres pendants
  périmés ; données dupliquées ; **monitorer la santé ÉCONOMIQUE, pas seulement le process**
  (« cron vert, logs remplis, aucune exception — et le bot ne faisait rien d'utile »).
- Watchdog : healthcheck périodique + restart automatique (docker-compose `restart: unless-stopped`) ;
  reprise = recharger l'état SQLite puis réconcilier AVANT toute décision.

---

## 8. Sécurité

- **Clés API** : trade-only (jamais withdrawal — « sinon un attaquant draine le compte »),
  whitelist IP (~70 % des exchanges le supportent), rotation trimestrielle, compte dédié,
  capital minimal. Sources : tradelink.pro/blog/how-to-secure-api-key ;
  docs.cdp.coinbase.com/get-started/authentication/security-best-practices ; darkbot.io.
- **Secrets** : `.env` hors git, jamais dans les logs, `pip-audit` sur les deps (Phase 9).
- **Injection via données externes** : l'injection indirecte de prompt est l'attaque n°1
  (OWASP LLM Top 10 2025) contre les agents ; le papier TradeTrap (arxiv 2512.02261) montre
  la manipulation d'agents de trading par contenu adversarial. **Application ici (R10)** :
  aucune donnée externe (news, API, web) n'entre dans les décisions de CE bot (signaux =
  fonctions déterministes des OHLCV) ; les limites de risque sont chargées une fois,
  immuables (pydantic frozen), et l'exécuteur les applique indépendamment des stratégies ;
  toutes les décisions (y compris refus) sont journalisées.
- Sources : sentinelone.com/cybersecurity-101/cybersecurity/prompt-injection-attack ;
  unit42.paloaltonetworks.com/ai-agent-prompt-injection ; arxiv.org/pdf/2512.02261.

---

## 9. Cadre légal / fiscal France-UE (informatif — **ceci n'est pas un conseil fiscal**)

- **Flat tax 2026 : 31,4 %** (12,8 % IR + 18,6 % prélèvements sociaux, CSG relevée au
  01/01/2026) sur les plus-values de cession d'actifs numériques des particuliers
  (art. 150 VH bis CGI) ; exonération si total des cessions ≤ 305 €/an ; option barème
  progressif possible ; **les échanges crypto-crypto ne sont pas imposables**, seule la
  conversion en fiat (ou l'achat de biens/services) déclenche l'imposition ; méthode du
  prix moyen pondéré d'acquisition du portefeuille global ; formulaires 2086 (cessions)
  et 3916-bis (comptes étrangers — Bybit inclus). Un bot qui multiplie les conversions
  crypto→fiat multiplie les événements imposables — à considérer avant tout passage réel.
  Sources concordantes : kraken.com/fr/learn/fiscalite-et-impot-crypto-en-france (lu) ;
  journalducoin.com/analyses/fiscalite-crypto-france-2026 ; waltio.com/fr/tout-savoir-sur-la-fiscalite-crypto.
- **MiCA** : cadre UE uniforme (transparence, agrément CASP, protection des consommateurs) ;
  pleine application 30/12/2024, fin de transition 01/07/2026 ; registre public ESMA.
  L'utilisateur final n'a pas d'obligation MiCA — c'est l'exchange qui doit être agréé ;
  d'où le choix d'un CASP agréé (Bybit EU). Sources : esma.europa.eu (lu) ;
  wikipedia.org/wiki/Markets_in_Crypto-Assets.
- Trading occasionnel de particulier = régime PFU ; une activité « professionnelle »
  (moyens sophistiqués, volumes) peut relever des BNC — zone grise à faire trancher par
  un professionnel si le live était un jour envisagé.

---

## Compteur Phase 1 — FINAL
- **WebSearch distinctes : 52** (≥ 50 exigées ✅)
- **Pages lues intégralement : 26** (24 WebFetch réussies + 2 PDF téléchargés et lus
  via extraction locale : arxiv 2009.12155, BIS WP 1087) (≥ 25 exigées ✅)
- Échecs notés : stratbase.ai (503), coinapi.io (403), ungeracademy/quantifiedstrategies
  (murs anti-bot) — remplacées par des sources équivalentes.
