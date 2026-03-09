# Audit de stabilité client / serveur

Fenêtre analysée:
- `2026-03-04` au `2026-03-08`
- horloge de référence: timestamps du conteneur Minecraft
- périmètre client local: `logs/*.log.gz`
- périmètre serveur distant: `/home/linux/codex-cobblemon/data/logs/*.log.gz`, `latest.log`, `docker compose logs cobblemon`

## Incidents corrélés

### 2026-03-07 01:03
- `date_heure`: `2026-03-07 01:03:04`
- `source`: `client + serveur`
- `joueur`: `Sondoku`
- `signature`: `session_disconnect_clean`
- `corrélation`: `corrélé`
- `sévérité`: `low`
- `preuve`:
  - client `2026-03-07-1.log.gz`: `01:03:04 Player logout received`
  - serveur `2026-03-07-1.log.gz`: `01:03:05 Sondoku lost connection: Disconnected`
- lecture:
  - fin de session propre
  - pas d'erreur serveur structurante dans la même minute

### 2026-03-07 23:18
- `date_heure`: `2026-03-07 23:18:07`
- `source`: `client + serveur`
- `joueur`: `Sondoku`
- `signature`: `session_disconnect_clean`
- `corrélation`: `corrélé`
- `sévérité`: `low`
- `preuve`:
  - client `2026-03-07-4.log.gz`: `23:18:07 Player logout received`
  - serveur `2026-03-07-4.log.gz`: `23:18:09 Sondoku lost connection: Disconnected`
- lecture:
  - même comportement qu'à `01:03`
  - les warnings voisins sur des entités `DISCARDED` ressemblent à du bruit de nettoyage d'entités, pas à un arrêt serveur

### 2026-03-08 11:23 à 11:24
- `date_heure`: `2026-03-08 11:24:16`
- `source`: `client + serveur`
- `joueur`: `Sondoku`
- `signature`: `session_disconnect_clean`
- `corrélation`: `corrélé`
- `sévérité`: `low`
- `preuve`:
  - client `2026-03-08-1.log.gz`: `11:24:16 Player logout received` puis fermeture propre DH/Xaero
  - serveur `2026-03-08-2.log.gz`: `11:24:16 Sondoku lost connection: Disconnected`
- lecture:
  - la validation demandée est positive: le `lost connection: Disconnected` serveur correspond exactement au logout client
  - aucun `Can't keep up!`, watchdog, ou exception serveur dans la même seconde

### 2026-03-08 13:41
- `date_heure`: `2026-03-08 13:41:16`
- `source`: `serveur`
- `joueur`: `Sondoku`
- `signature`: `server_watchdog_crash_during_mounted_movement`
- `correlation`: `serveur-only`
- `severite`: `critical`
- `preuve`:
  - `latest.log`: `A single server tick took 120.00 seconds`
  - `latest.log`: `Considering it to be crashed, server will forcibly shutdown`
  - `data/crash-reports/crash-2026-03-08_13.41.16-server.txt`: `Player Count: 1 / 4; [Sondoku ... x=-308.06, y=75.83, z=286.46]`
  - `data/crash-reports/crash-2026-03-08_13.41.16-server.txt`: pile bloquee sur `getChunkBlocking` puis `Lithium` `ChunkAwareBlockCollisionSweeper`
- lecture:
  - crash serveur confirme par watchdog
  - le thread principal s'est bloque pendant un traitement de mouvement/collision avec chargement de chunk synchrone
  - ce n'est pas un OOM: la memoire restait sous la limite du conteneur

### 2026-03-08 13:52 a 13:56
- `date_heure`: `2026-03-08 13:54:07`
- `source`: `serveur`
- `joueur`: `Sondoku`
- `signature`: `mounted_flight_chunk_desync`
- `correlation`: `serveur-only`
- `severite`: `high`
- `preuve`:
  - `latest.log`: `Sondoku moved too quickly! -32.92325151314344,0.7540159831771831,-17.286440199529352`
  - `latest.log`: rafale `Garchomp (vehicle of Sondoku) moved too quickly! ...`
  - `latest.log`: `Can't keep up! Is the server overloaded? Running 5841ms or 116 ticks behind`
  - symptome joueur rapporte: monde pas encore charge, disparition apparente de la monture
- lecture:
  - signature reproductible sans nouveau crash immediat
  - le bug se manifeste d'abord comme une desynchronisation monture/joueur sous vol rapide, puis comme du lag serveur
  - le crash watchdog de `13:41` ressemble a la version extreme du meme probleme

## Anomalies client sans impact serveur

### 2026-03-07 19:23
- `date_heure`: `2026-03-07 19:23:08`
- `source`: `client`
- `joueur`: `Sondoku`
- `signature`: `client_startup_render_failure`
- `corrélation`: `client-only`
- `sévérité`: `medium`
- `preuve`:
  - client `2026-03-07-3.log.gz`: `Failed to resolve uniform inPaleGarden`
  - client `2026-03-07-3.log.gz`: `[FANCYMENU] Failed to read text content/texture from file`
- lecture:
  - incident de pile graphique/UI côté client
  - pas de preuve serveur associée
  - cause probable: shader Iris incompatible + assets FancyMenu manquants dans le profil Modrinth local

### Warnings client répétés mais non bloquants
- `signature`: `supplementaries_unknown_target`, `unknown_entity_passengers`
- `corrélation`: `client-only`
- `sévérité`: `low`
- `preuve`:
  - `2026-03-07-1.log.gz`, `2026-03-07-4.log.gz`, `2026-03-08-1.log.gz`
- lecture:
  - bruit de synchronisation entités/attachments
  - rien ne relie ces warnings à un arrêt ou crash serveur sur les fenêtres corrélées

## Anomalies serveur sans impact joueur confirmé

### Lag serveur récurrent sur la fenêtre
- `source`: `serveur`
- `signature`: `server_tick_lag`
- `corrélation`: `serveur-only`
- `sévérité`: `high`
- `preuve`:
  - `2026-03-05`: `2` warnings `Can't keep up!`
  - `2026-03-06`: `125` warnings `Can't keep up!`
  - `2026-03-07`: `137` warnings `Can't keep up!`
  - `2026-03-08`: `12` warnings `Can't keep up!`
- lecture:
  - la stabilité serveur est déjà dégradée avant l'épisode `Distant Horizons` du `8 mars 2026`
  - le problème de performance n'est donc pas né avec `Distant Horizons`
  - en revanche, `Distant Horizons` ajoute ensuite une nouvelle classe d'erreurs serveur, ce qui augmente le risque global

### 2026-03-08 11:38 à 11:49
- `date_heure`: `2026-03-08 11:49:04`
- `source`: `serveur`
- `joueur`: `Sondoku`
- `signature`: `server_restart_interrupting_player`
- `corrélation`: `serveur-only`
- `sévérité`: `medium`
- `preuve`:
  - serveur `2026-03-08-2.log.gz`: `11:49:04 Stopping the server`
  - serveur `2026-03-08-2.log.gz`: `11:49:04 Sondoku lost connection: Server closed`
  - serveur `latest.log`: nouveau boot à `11:49:36`
- lecture:
  - arrêt propre suivi d'un redémarrage propre
  - pas de signature de crash
  - impact joueur réel: session interrompue par fermeture serveur
- limite:
  - aucun log client local couvrant la reprise `11:38` à `11:49`; cette tranche est donc documentée uniquement côté serveur

### 2026-03-08 11:56 et après
- `date_heure`: `2026-03-08 11:56:02`
- `source`: `serveur`
- `joueur`: `Sondoku` présent en ligne
- `signature`: `distant_horizons_pregen_errors`
- `corrélation`: `serveur-only`
- `sévérité`: `medium`
- `preuve`:
  - `latest.log`: `Generation for section ... has expired!`
  - `latest.log`: `Unable to close Phantom Array, error: [Null phantom checkout, object is being closed multiple times.]`
  - `latest.log`: `C2ME missing`
- lecture:
  - `Distant Horizons` génère des erreurs répétées en serveur pendant qu'un joueur est connecté
  - aucun `Can't keep up!` ni déconnexion immédiate corrélée à ces erreurs dans l'échantillon
  - le risque principal est une dégradation active de stabilité/performance, pas un crash déjà confirmé
- configuration effective relevee ensuite:
  - `enableDistantGeneration = true`
  - `distantGeneratorMode = "INTERNAL_SERVER"`
  - `maxGenerationRequestDistance = 4096`
  - `realTimeUpdateDistanceRadiusInChunks = 256`
- implication:
  - meme hors pregen manuel, DH reste capable de demander generation/chargement loin autour du joueur
  - cette capacite est coherente avec un changement de comportement apparu apres l'installation serveur du mod

### 2026-03-08 13:52 a 13:57
- `source`: `serveur`
- `signature`: `mounted_vehicle_move_too_quickly`
- `correlation`: `serveur-only`
- `severite`: `high`
- `preuve`:
  - `latest.log`: dizaines de lignes `Garchomp (vehicle of Sondoku) moved too quickly!`
  - `latest.log`: `Can't keep up!` a `13:54:07` puis `13:55:18`
  - `docker stats`: pic observe `CPU=393.94%`, `MEM=5.398GiB / 7.641GiB`
- lecture:
  - la charge grimpe nettement pendant les reproductions de vol rapide
  - la saturation est coherente avec un serveur qui tente de rattraper une desynchronisation de mouvement sur monture
  - la memoire reste stable, ce qui renforce l'hypothese `mouvement/chunk loading`, pas `OOM`

### 2026-03-08 14:20 a 14:29
- `source`: `serveur`
- `signature`: `garchomp_mount_entity_discarded_under_pre_existing_only`
- `correlation`: `serveur-only`
- `severite`: `critical`
- `preuve`:
  - `latest.log`: mode DH bascule en `PRE_EXISTING_ONLY` avant ce test
  - `latest.log`: `Entity PokemonEntity['Garchomp' ... removed=DISCARDED] wasn't found in section ... (destroying due to DISCARDED)`
  - `latest.log`: rafales `Garchomp (vehicle of Sondoku) moved too quickly!`
  - `latest.log`: `Sondoku moved too quickly! ...`
  - `latest.log`: `Sondoku fell from a high place`
- lecture:
  - la disparition de monture est confirmee cote serveur: l'entite `Garchomp` est reellement detruite
  - le bug persiste meme quand `Distant Horizons` n'est plus en `INTERNAL_SERVER`
  - `Distant Horizons` n'est donc pas la cause unique; au mieux un facteur aggravant precedent

### 2026-03-08 14:40 et après
- `source`: `serveur`
- `signature`: `multi_player_mount_sync_failure_and_tps_collapse`
- `correlation`: `serveur-only`
- `severite`: `critical`
- `preuve`:
  - `latest.log`: `Can't keep up!` jusqu'a `193 ticks behind`
  - `latest.log`: `TiidyMan moved wrongly!`
  - `latest.log`: `Entity PokemonEntity['Aerodactyl' ... removed=DISCARDED]`
  - `latest.log`: `Entity PokemonEntity['Blaziken' ... removed=DISCARDED]`
  - `latest.log`: nouvelles rafales `Garchomp (vehicle of Sondoku) moved too quickly!`
- lecture:
  - le probleme depasse desormais `Garchomp` seul
  - plusieurs montures / entites Cobblemon sont detruites `DISCARDED`
  - la degradation devient collective: au moins deux joueurs actifs et symptomes de mouvement anormal sur plusieurs entites/joueurs
  - quand les joueurs rapportent une baisse de FPS simultanee, le serveur montre en fait un effondrement TPS majeur en parallele

## Hypothèses prioritaires

### 1. La majorité des coupures corrélées visibles sont des déconnexions propres
- confiance: `haute`
- base:
  - concordance exacte client/serveur à `2026-03-07 01:03`, `2026-03-07 23:18`, `2026-03-08 11:24`

### 2. L'incident le plus sérieux côté client est indépendant du serveur
- confiance: `haute`
- base:
  - erreur `Iris` + assets `FancyMenu` manquants sans trace serveur corrélée à `2026-03-07 19:23`

### 3. Le risque principal côté serveur se concentre autour de `Distant Horizons`
- confiance: `moyenne`
- base:
- un lag serveur récurrent existe déjà sur `2026-03-05` à `2026-03-08`
- mode `INTERNAL_SERVER` confirmé
- changements de mode `PRE_EXISTING_ONLY` puis retour `INTERNAL_SERVER`
- erreurs `Unable to close Phantom Array`
- warnings `Generation ... expired`
- activité observée pendant qu'un joueur est connecté
- conclusion:
  - `Distant Horizons` n'explique pas à lui seul toute l'instabilité historique
  - mais il devient le meilleur suspect d'aggravation et de complexification du problème après son activation serveur

### 5. Le bug de stabilite le plus reproductible hors `Distant Horizons` est le vol monte rapide
- confiance: `haute`
- base:
  - crash watchdog confirme a `13:41:16`
  - stack bloquee sur `getChunkBlocking` et collisions/mouvement `Lithium`
  - rafales `Garchomp (vehicle of Sondoku) moved too quickly!` a `13:54:07` et `13:56:36`
  - pics `Can't keep up!` pendant ces rafales
  - symptome joueur: monde non charge et disparition apparente du Pokemon monte
- conclusion:
  - hors `Distant Horizons`, le meilleur suspect est un probleme de deplacement monte rapide a travers des chunks non prets
  - `Lithium` est un facteur d'attention serieux car il apparait explicitement dans la pile du crash
  - l'absence de `C2ME` peut aggraver les blocages de chargement de chunks, mais ne suffit pas seule a expliquer la disparition de monture

### 6. L'apparition du bug apres l'installation serveur de `Distant Horizons` est compatible avec sa config actuelle
- confiance: `haute`
- base:
  - ordre d'apparition rapporte par le joueur
  - `DistantHorizons.toml`:
    - `enableDistantGeneration = true`
    - `distantGeneratorMode = "INTERNAL_SERVER"`
    - `maxGenerationRequestDistance = 4096`
    - `realTimeUpdateDistanceRadiusInChunks = 256`
  - warnings serveur:
    - `C2ME missing`
    - `Unknown Chunk Generator detected ... Distant Generation May Fail!`
- conclusion:
  - meme si le symptome visible est un bug de vol monte rapide, la mise en place de DH serveur a probablement change la pression de chargement/generation de chunks autour du joueur
  - le meilleur candidat de cause systemique est desormais `Distant Horizons` cote serveur, avant `Lithium`

### 7. Le meilleur suspect final est maintenant le systeme de monture Cobblemon 1.7.x, avec `Distant Horizons` comme aggravant possible
- confiance: `haute`
- base:
  - le bug persiste en `PRE_EXISTING_ONLY`
  - `Garchomp` est explicitement detruit `removed=DISCARDED`
  - `Garchomp (vehicle of Sondoku) moved too quickly!` apparait juste avant
  - des tickets publics Cobblemon 1.7.x documentent deja plusieurs regressions de montures Garchomp / logique de ride
- conclusion:
  - la cause racine la plus probable est un bug Cobblemon sur la logique de monture volante rapide / etat d'entite
  - la capacite serveur et `Distant Horizons` peuvent empirer le phenomene, mais n'expliquent pas a eux seuls la destruction de l'entite
  - le fait que `Aerodactyl` et d'autres entites Cobblemon soient maintenant aussi touches renforce l'hypothese d'un probleme general de synchronisation d'entites montees ou proches du joueur

### 4. L'arrêt `11:49:04` du 8 mars 2026 est un redémarrage propre, pas un crash
- confiance: `haute`
- base:
  - séquence complète d'arrêt propre
  - sauvegarde des joueurs et mondes
  - nouveau démarrage `latest.log` à `11:49:36`

## Actions recommandées

### Priorité immédiate
- suspendre les tâches `Distant Horizons` serveur / prégen tant que les erreurs `Phantom Array` persistent
- traiter le lag de fond comme sujet séparé, car il est visible avant l'activation `Distant Horizons`
- éviter de lancer ou modifier des pré-générations `Distant Horizons` en présence de joueurs tant que les erreurs `Phantom Array` persistent
- considérer `Distant Horizons` serveur comme le premier suspect d'aggravation récente, pas comme l'unique cause
- traiter separement le bug `vol monte rapide -> moved too quickly! -> Can't keep up! -> risque watchdog`
- considerer `Lithium` comme le premier candidat de test pour un conflit sur collisions/mouvement montes
- apres test A/B negatif sur `Lithium`, remonter `Distant Horizons` serveur au rang de premier suspect global
- apres test `PRE_EXISTING_ONLY` negatif, remonter `Cobblemon` montures au rang de premier suspect global
- conserver comme baseline d'observation:
  - host Linux avec `16 Go` de RAM
  - heap Minecraft `MEMORY=6G`
  - `Distant Horizons` en `PRE_EXISTING_ONLY`
  - `Lithium` revenu au defaut
  - gestion principale via `192.168.1.19` (Ethernet), secours `192.168.1.23` (Wi-Fi)

### Vérifications ciblées
- quantifier le lag hors `Distant Horizons`:
  - périodes exactes des `Can't keep up!`
  - joueurs connectés
  - tâches actives (`Chunky`, commandes admin, génération, sauvegardes)
- reproduire en session courte avec surveillance des logs pour confirmer si chaque disparition de monture est precedee par `Garchomp (vehicle of Sondoku) moved too quickly!`
- tester un demarrage sans optimisations `Lithium` sur collisions/mouvement pour voir si le crash watchdog et la desynchronisation disparaissent
- verifier si la zone autour de `x=-320`, `z=270-286` ou des zones encore peu chargees concentrent davantage les reproductions
- tester la mitigation la plus propre cote serveur:
  - soit `enableDistantGeneration = false`
  - soit `distantGeneratorMode = "PRE_EXISTING_ONLY"`
  - puis refaire exactement le meme vol rapide
- conserver `PRE_EXISTING_ONLY` a court terme car c'est plus sur que `INTERNAL_SERVER`, meme si cela ne corrige pas le bug de monture
- auditer maintenant le versant `Cobblemon`:
  - tickets publics
  - regressions connues de ride en `1.7.x`
  - comportements lies a `Garchomp`, aux montures volantes et aux placeholders d'entite
- reproduire une session courte avec `Distant Horizons` serveur inactif puis actif pour comparer:
  - déconnexions
  - charge
  - bruit `DH-World Gen`
- vérifier si l'arrêt `11:49` était une maintenance volontaire; les logs seuls montrent un arrêt propre mais pas son déclencheur humain
- corriger côté client:
  - pack shader Iris ou désactivation du shader fautif
  - assets `FancyMenu` manquants

### Suivi
- relancer `py -3 tools/stability_audit.py --start-date <date> --end-date <date> --write`
- conserver le tri:
  - `corrélé`
  - `client-only`
  - `serveur-only`

## Baseline d'observation a conserver

- date de gel operationnel: `2026-03-09`
- objectif: observer `3` a `5` jours sans nouveau changement de configuration, sauf incident majeur
- etat retenu:
  - host Linux: `16 Go` RAM physique (`2 x 8 Go Crucial CT102464BF160B`, `1600 MT/s`)
  - reseau principal: `Ethernet enp2s0`, IP LAN `192.168.1.19`
  - reseau de secours: `Wi-Fi wlp3s0`, IP LAN `192.168.1.23`
  - Minecraft: `MEMORY=6G`
  - `Distant Horizons`: `PRE_EXISTING_ONLY`
  - `Lithium`: configuration par defaut
- indicateurs a suivre pendant la periode:
  - volume de `Can't keep up!`
  - volume de `removed=DISCARDED`
  - occurrence de `moved too quickly!` / `moved wrongly!`
  - ressenti multi-joueurs
- regle:
  - ne pas retoucher la performance ou les mods avant d'avoir une nouvelle base de comparaison exploitable
