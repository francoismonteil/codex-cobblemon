# Addons rollout journal

Objectif:
- consigner l'execution reelle des lots addons Cobblemon
- garder une trace courte des validations, backups, checks et suites

Base cible:
- Minecraft `1.21.1`
- Loader `Fabric`
- Cobblemon `1.7.3`

## Known issues

### Cobblemon Quick Battle
- Mod: `Cobblemon Quick Battle`
- Version: `1.2.5`
- Symptome: `Multi Exp / Exp. Share` ne partage pas toujours l'XP en `Quick Battle`, alors que le partage fonctionne en combat normal
- Impact: `visible gameplay`
- Contournement: `utiliser les combats normaux pour tout ce qui depend du Multi Exp`
- Statut: `known_issue_accepted`
- Declencheur de retrait: `autres regressions XP/EV, duplication, perte d'XP, soft-lock, ou bug de combat non contournable`

### Blue's Cobblemon Utilities
- Mod: `Blue's Cobblemon Utilities`
- Version: `4.0.0`
- Symptome: erreurs de chargement sur les fonctions `bluecustomitems:addon_support/size_variation/convert/*`
- Impact: `partiel et non encore reproduit en usage joueur`
- Contournement: `considerer size_variation comme experimental / non supporte tant qu'il n'est pas revalide`
- Statut: `restricted_functionality`
- Declencheur de retrait: `echec joueur reproductible, perte d'objet, crash, ou extension des erreurs a d'autres familles de fonctions`

### Cobblemon Raid Dens
- Mod: `Cobblemon Raid Dens`
- Version: `0.8.1+1.21.1`
- Symptome: advancements de raid qui referencent des items `Mega Showdown` absents
- Impact: `non bloquant`
- Contournement: `ignorer ces advancements tant qu'aucun impact de raid ou de recompense n'est observe`
- Statut: `accepted_log_noise`
- Declencheur de retrait: `probleme concret de raid, de recompense ou de progression`

### Supplementaries
- Mod: `Supplementaries`
- Version: `1.21-3.5.25-fabric`
- Symptome: recettes `pancake` / `planter` retirees et erreurs de tags `dyed/brown`
- Impact: `non bloqueur a ce stade`
- Contournement: `surveiller et n'ouvrir un chantier que si un joueur signale une recette ou un item manquant`
- Statut: `accepted_log_noise`
- Declencheur de retrait: `recettes ou items de gameplay reellement casses pour les joueurs`

### Flan
- Mod: `Flan`
- Version: `1.21.1-1.12.1-fabric`
- Symptome: parse errors sur des permissions qui pointent vers des mods absents (`AE2`, `Mekanism`, `Taterzens`)
- Impact: `bruit de configuration`
- Contournement: `aucune action prod immediate`
- Statut: `accepted_log_noise`
- Declencheur de retrait: `echec reel des claims, des permissions ou d'un outil supporte`

### Disconnect packet
- Mod: `server networking`
- Version: `n/a`
- Symptome: `Sending unknown packet 'clientbound/minecraft:disconnect'`
- Impact: `probables tentatives de connexion non conformes`
- Contournement: `verifier d'abord la conformite du pack client avant d'escalader`
- Statut: `accepted_log_noise`
- Declencheur de retrait: `joueur avec le bon pack incapable de se connecter de facon reproductible`

## Lot 1 - Cobblemon Pokenav

Statut:
- `deployed`
- `validated`

Execution:
- maintenance effectuee le `2026-03-04`
- script applique: `./infra/mods-install-addon-lot1-pokenav.sh`
- checker cumulatif: `./infra/mods-check-addons-rollout.sh --through-lot 1`
- resultat checker: `expected=21 ok=21 missing=0 hash_mismatch=0`

Preuves operationnelles:
- backup pre-maintenance pris sur l'hote distant:
  - `backups/backup-20260304-044139.tar.gz`
- le serveur a redemarre correctement
- les logs montrent le chargement de `cobblenav 2.2.5`
- le serveur a atteint `Done (...)!`
- etat final apres redemarrage:
  - `status=running`
  - `health=healthy`

Validation fonctionnelle:
- lot teste en production pendant la fenetre d'observation prevue
- tests utilisateur valides
- aucun blocage retenu avant ouverture du lot suivant

Decision:
- lot `1` accepte comme baseline active
- pas de rollback necessaire

## Lot 2 - APS Trophies

Statut:
- `deployed`
- `validated`

Perimetre retenu:
- serveur:
  - `APS Trophies 1.1.1`
- client:
  - `APS Trophies 1.1.1`
  - `Catch Indicator 1.4.1` en option recommandee, non bloquante

Preflight attendu avant maintenance:
- script verifie:
  - `bash -n ./infra/mods-install-addon-lot2-aps-trophies.sh`
- artefact verifie sur l'hote distant:
  - URL accessible
  - SHA256 conforme au verrou `1.1.1`

Execution:
- maintenance effectuee le `2026-03-04`
- script applique: `./infra/mods-install-addon-lot2-aps-trophies.sh`
- checker cumulatif: `./infra/mods-check-addons-rollout.sh --through-lot 2`
- resultat checker: `expected=22 ok=22 missing=0 hash_mismatch=0`

Preuves operationnelles:
- backup pre-maintenance pris sur l'hote distant:
  - `backups/backup-20260304-051738.tar.gz`
- le serveur a redemarre correctement
- etat final apres redemarrage:
  - `status=running`
  - `health=healthy`
- annonce Discord de maintenance postee
- annonce Discord de reouverture postee

Validation immediate:
- le lot est techniquement actif
- `Catch Indicator` reste optionnel cote client
- la fenetre d'observation `24h` a ete ouverte puis terminee

Validation fonctionnelle:
- attribution d'un trophee de test
- pose / affichage / conservation du trophee
- connexion d'un joueur sans `Catch Indicator`
- connexion d'un joueur avec `Catch Indicator`
- tests utilisateur valides
- aucun blocage retenu avant ouverture du lot suivant

Decision:
- lot `2` accepte comme baseline active
- pas de rollback necessaire

## Lot 3 - Cobblemon Quick Battle

Statut:
- `deployed`
- `validated`

Perimetre retenu:
- serveur:
  - `Cobblemon Quick Battle 1.2.5`
- client:
  - `Cobblemon Quick Battle 1.2.5`

Preflight:
- script verifie:
  - `bash -n ./infra/mods-install-addon-lot3-quick-battle.sh`
- artefact verifie sur l'hote distant:
  - URL accessible
  - SHA256 conforme au verrou `1.2.5`

Execution:
- maintenance effectuee le `2026-03-04`
- script applique: `./infra/mods-install-addon-lot3-quick-battle.sh`
- checker cumulatif: `./infra/mods-check-addons-rollout.sh --through-lot 3`
- resultat checker: `expected=23 ok=23 missing=0 hash_mismatch=0`

Preuves operationnelles:
- backup pre-maintenance pris sur l'hote distant:
  - `backups/backup-20260304-055019.tar.gz`
- le serveur a redemarre correctement
- etat final apres redemarrage:
  - `status=running`
  - `health=healthy`
- annonce Discord de maintenance postee
- annonce Discord de reouverture postee

Validation immediate:
- le lot est techniquement actif
- la fenetre d'observation `48h` a ete ouverte puis terminee

Validation fonctionnelle:
- combat rapide fonctionnel
- combat classique non regresse
- capture apres combat OK
- pas de duplication ou soft-lock
- pas de desync visible client/serveur
- tests utilisateur valides
- aucun blocage retenu avant ouverture du lot suivant

Decision:
- lot `3` accepte comme baseline active
- pas de rollback necessaire

## Lot 4 - Cobbleloots

Statut:
- `deployed`
- `validated`

Perimetre retenu:
- serveur:
  - `Cobbleloots 2.2.2`
- client:
  - `Cobbleloots 2.2.2`

Preflight:
- script verifie:
  - `bash -n ./infra/mods-install-addon-lot4-cobbleloots.sh`
- artefact verifie sur l'hote distant:
  - URL accessible
  - SHA256 conforme au verrou `2.2.2`

Execution:
- maintenance effectuee le `2026-03-04`
- script applique: `./infra/mods-install-addon-lot4-cobbleloots.sh`
- checker cumulatif: `./infra/mods-check-addons-rollout.sh --through-lot 4`
- resultat checker: `expected=24 ok=24 missing=0 hash_mismatch=0`

Preuves operationnelles:
- backup pre-maintenance pris sur l'hote distant:
  - `backups/backup-20260304-061725.tar.gz`
- le serveur a redemarre correctement
- etat final apres redemarrage:
  - `status=running`
  - `health=healthy`
- annonce Discord de maintenance postee
- annonce Discord de reouverture postee

Validation immediate:
- le lot est techniquement actif
- la fenetre d'observation `72h` a ete ouverte puis terminee

Validation fonctionnelle:
- generation de points/balls de loot dans de nouveaux chunks
- coherence des recompenses
- absence d'erreurs repetees dans les tables/configs
- pas de regression du loot vanilla ou Cobblemon existant
- extension du monde et pre-generation observees sans erreur bloquante liee a `Cobbleloots`
- logs serveur coherents:
  - datapack `cobbleloots` charge automatiquement
  - `22 Loot Ball data definitions` chargees
  - `36 injected loot tables`
- pas d'erreur de resolution de mods imputable au lot 4

Decision:
- lot `4` accepte comme baseline active
- pas de rollback necessaire

## Lot 5 - Raid Dens

Statut:
- `deployed`
- `in_observation`

Perimetre retenu:
- serveur:
  - `GeckoLib 4.8.4`
  - `Cobblemon Raid Dens 0.8.1+1.21.1`
- client:
  - `GeckoLib 4.8.4`
  - `Cobblemon Raid Dens 0.8.1+1.21.1`

Preflight:
- script verifie:
  - `bash -n ./infra/mods-install-addon-lot5-raiddens.sh`
- artefacts verifies sur l'hote distant:
  - `GeckoLib` URL accessible
  - `GeckoLib` SHA256 conforme
  - `Raid Dens` URL accessible
  - `Raid Dens` SHA256 conforme

Execution:
- maintenance effectuee le `2026-03-04`
- script applique: `./infra/mods-install-addon-lot5-raiddens.sh`
- checker cumulatif: `./infra/mods-check-addons-rollout.sh --through-lot 5`
- resultat checker: `expected=26 ok=26 missing=0 hash_mismatch=0`

Preuves operationnelles:
- backup pre-maintenance pris sur l'hote distant:
  - `backups/backup-20260304-071541.tar.gz`
- le serveur a redemarre correctement
- etat final apres redemarrage:
  - `status=running`
  - `health=healthy`
- annonce Discord de maintenance postee
- annonce Discord de reouverture postee
- logs serveur coherents:
  - `Initialising cobblemonraiddens`
  - `Registered 879 raid bosses`

Validation immediate:
- le lot est techniquement actif
- la fenetre d'observation longue est ouverte

Validation fonctionnelle attendue:
- nouvelles dens dans des chunks non critiques
- entree/sortie d'un raid
- recompenses coherentes
- pas de corruption de chunk
- pas de spam logs lie a generation / entites

## Lot 6 - Blue's Cobblemon Utilities

Statut:
- `deployed`
- `in_observation`

Perimetre retenu:
- serveur:
  - `Blue's Cobblemon Utilities 4.0.0` (datapack zip)
- client:
  - aucun jar obligatoire dans ce rollout

Preflight:
- script verifie:
  - `bash -n ./infra/mods-install-addon-lot6-blues-utilities.sh`
- artefact verifie sur l'hote distant:
  - URL accessible
  - SHA256 conforme au verrou `4.0.0`
- chemins verifies sur l'hote distant:
  - `./data/world`
  - `./data/world/datapacks`

Execution:
- maintenance effectuee le `2026-03-04`
- script applique: `./infra/mods-install-addon-lot6-blues-utilities.sh`
- checker cumulatif: `./infra/mods-check-addons-rollout.sh --through-lot 6`
- resultat checker: `expected=27 ok=27 missing=0 hash_mismatch=0`

Preuves operationnelles:
- backup pre-maintenance pris sur l'hote distant:
  - `backups/backup-20260304-073612.tar.gz`
- le serveur a redemarre correctement
- etat final apres redemarrage:
  - `status=running`
  - `health=healthy`
- annonce Discord de maintenance postee
- annonce Discord de reouverture postee
- datapack confirme actif:
  - `file/blues-cobblemon-utilities-4.0.0.zip (world)`

Validation immediate:
- le lot est techniquement actif
- la fenetre d'observation restreinte est ouverte
- rappel:
  - retrait infra facile
  - retour gameplay exact non garanti sans backup si des effets sont deja appliques

Validation fonctionnelle attendue:
- datapack visible dans `datapack list enabled`
- fonctions autorisees testees sur perimetre restreint
- desactivation possible si besoin
- pas d'erreur datapack apres `reload` / reboot

## Realignement de roadmap - 2026-03-04

Decision:
- les lots `7` et `8` du plan actif sont reassignes vers une piste cuisine/agriculture
- nouveaux lots actifs:
  - lot `7`: `Farmer's Delight Refabricated 3.2.5`
  - lot `8`: `Bookshelf 21.1.81`, `Prickle 21.1.11`, `Botany Pots 21.1.41`, `Cobblemon Botany Pots 1.0.1`

Sortis du plan actif:
- `CobbledGacha`
- `Cobblemon: Shiny Cookie`

Bloques / exclus du plan actif:
- `Tomtaru's Cobblemon & Farmer's Delight Tweaks`: NeoForge uniquement en `1.21.1`
- `CobbleCuisine`: ligne Cobblemon `1.7.x` publiee en alpha/rc
- `CobbleFoods`: pas de build `1.21.1`

Trace:
- lockfile mis a jour: `audit/addons-compat-lock-20260304.md`
- rollout monde actuel mis a jour: `runbooks/addons-rollout-current-world.md`
- pack client mis a jour: `runbooks/client-pack-addons-rollout.md`

## Reouverture des lots 9 et 10 - 2026-03-04

Decision:
- `CobbledGacha` et `Cobblemon: Shiny Cookie` sont reintegres au plan actif
- nouveaux lots actifs:
  - lot `9`: `CobbledGacha 3.0.2`
  - lot `10`: `Cobblemon: Shiny Cookie 0.0.1`

Motif:
- le risque de persistance gameplay est explicitement accepte
- les deux mods sont donc reevalues comme deployables en lots controles, sans exigence de reversibilite gameplay stricte

Statut:
- lot `9`: `defined`, `not_opened`
- lot `10`: `defined`, `not_opened`

Trace:
- scripts ajoutes:
  - `./infra/mods-install-addon-lot9-gacha-machine.sh`
  - `./infra/mods-install-addon-lot10-shiny-cookie.sh`
- runbooks ajoutes:
  - `runbooks/addons-rollout-lot9-gacha-machine.md`
  - `runbooks/addons-rollout-lot10-shiny-cookie.md`
- checker et plan actif mis a jour pour accepter `--through-lot 10`

## Lot 7 - Farmer's Delight Refabricated

Statut:
- `deployed`
- `validated`

Perimetre retenu:
- serveur:
  - `Farmer's Delight Refabricated 3.2.5`
- client:
  - `Farmer's Delight Refabricated 3.2.5`

Preflight:
- script verifie:
  - `bash -n ./infra/mods-install-addon-lot7-farmers-delight.sh`
- artefact verifie:
  - URL accessible
  - SHA256 conforme au verrou `3.2.5`

Execution:
- maintenance effectuee le `2026-03-04`
- script applique: `./infra/mods-install-addon-lot7-farmers-delight.sh`
- checker cumulatif: `./infra/mods-check-addons-rollout.sh --through-lot 7`
- resultat checker: `expected=28 ok=28 missing=0 hash_mismatch=0`

Preuves operationnelles:
- backup pre-maintenance pris sur l'hote distant:
  - `backups/backup-20260304-085727.tar.gz`
- le serveur a redemarre correctement
- etat final apres redemarrage:
  - `status=running`
  - `health=healthy`
- annonce Discord de maintenance postee
- annonce Discord de reouverture postee
- message de reouverture envoye en jeu
- logs serveur coherents:
  - `farmersdelight 1.21.1-3.2.5+refabricated`
  - `Loaded config farmersdelight-common.json`
  - `Found new data pack farmersdelight, loading it automatically`
  - `Done (5.374s)!`

Validation immediate:
- le lot est techniquement actif
- la fenetre d'observation `48h` est ouverte

Validation fonctionnelle attendue:
- connexion client avec `Farmer's Delight Refabricated 3.2.5`
- blocs de cuisine placables et utilisables
- recettes visibles et craftables
- pas de crash, desync d'inventaire ou souci de recette

Decision:
- tests utilisateur valides
- lot `7` accepte comme baseline active
- pas de rollback necessaire
- lot `8` peut maintenant etre prepare pour maintenance

## Lot 8 - Botany Pots

Statut:
- `deployed`
- `in_observation`

Perimetre retenu:
- serveur:
  - `Architectury API 13.0.8+fabric`
  - `Bookshelf 21.1.81`
  - `Prickle 21.1.11`
  - `Botany Pots 21.1.41`
  - `Cobblemon Botany Pots 1.0.1`
- client:
  - `Architectury API 13.0.8+fabric`
  - `Bookshelf 21.1.81`
  - `Prickle 21.1.11`
  - `Botany Pots 21.1.41`
  - `Cobblemon Botany Pots 1.0.1`

Preflight:
- script verifie:
  - `bash -n ./infra/mods-install-addon-lot8-botany-pots.sh`
- artefacts verifies:
  - `Architectury API 13.0.8+fabric` URL accessible et SHA256 conforme
  - `Bookshelf 21.1.81` URL accessible et SHA256 conforme
  - `Prickle 21.1.11` URL accessible et SHA256 conforme
  - `Botany Pots 21.1.41` URL accessible et SHA256 conforme
  - `Cobblemon Botany Pots 1.0.1` URL accessible et SHA256 conforme

Execution:
- maintenance effectuee le `2026-03-04`
- script applique: `./infra/mods-install-addon-lot8-botany-pots.sh`
- checker cumulatif: `./infra/mods-check-addons-rollout.sh --through-lot 8`
- resultat checker final: `expected=33 ok=33 missing=0 hash_mismatch=0`

Incident corrige pendant maintenance:
- premier boot refuse:
  - `Cobblemon Botany Pots 1.0.1` demandait `Architectury >= 13.0.8`
- correctif applique:
  - ajout de `Architectury API 13.0.8+fabric` au lot `8`
  - redeploiement du repo vers l'hote
  - reexecution du script lot `8`

Preuves operationnelles:
- backup pre-maintenance pris sur l'hote distant:
  - `backups/backup-20260304-091958.tar.gz`
- le serveur a redemarre correctement apres correction
- etat final apres redemarrage:
  - `status=running`
  - `health=healthy`
- annonce Discord de maintenance postee
- annonce Discord de reouverture postee avec pile client corrigee
- message de reouverture envoye en jeu
- logs serveur coherents:
  - `architectury 13.0.8`
  - `botanypots 21.1.41`
  - `cobblemon_pots 1.0.1`
  - `Loaded 1 botany pots plugins!`
  - `Found new data pack botanypots`
  - `Found new data pack cobblemon_pots`
  - `Done (5.273s)!`

Validation immediate:
- le lot est techniquement actif
- la fenetre d'observation `72h` est ouverte

Validation fonctionnelle attendue:
- client avec la pile complete:
  - `Architectury API 13.0.8+fabric`
  - `Bookshelf 21.1.81`
  - `Prickle 21.1.11`
  - `Botany Pots 21.1.41`
  - `Cobblemon Botany Pots 1.0.1`
- pot placable et fonctionnel
- culture Cobblemon dans les pots OK
- automation simple OK
- pas de crash, duplication ou comportement anormal

## Lot 9 - CobbledGacha

Statut:
- `deployed`
- `in_observation`

Perimetre retenu:
- serveur:
  - `CobbledGacha 3.0.2`
- client:
  - `CobbledGacha 3.0.2`

Preflight:
- script verifie:
  - `bash -n ./infra/mods-install-addon-lot9-gacha-machine.sh`
- artefact verifie:
  - URL accessible
  - SHA256 conforme au verrou `3.0.2`

Execution:
- maintenance effectuee le `2026-03-04`
- script applique: `./infra/mods-install-addon-lot9-gacha-machine.sh`
- checker cumulatif: `./infra/mods-check-addons-rollout.sh --through-lot 9`
- resultat checker: `expected=34 ok=34 missing=0 hash_mismatch=0`

Preuves operationnelles:
- backup pre-maintenance pris sur l'hote distant:
  - `backups/backup-20260304-122525.tar.gz`
- le serveur a redemarre correctement
- etat final apres redemarrage:
  - `status=running`
  - `health=healthy`
- annonce Discord de maintenance postee
- annonce Discord de reouverture postee
- logs serveur coherents:
  - `Cobbled Gacha Machine Fabric initialized!`
  - `Done (6.045s)!`

Validation immediate:
- le lot est techniquement actif
- la fenetre d'observation `48h` est ouverte

Validation fonctionnelle attendue:
- client avec `CobbledGacha 3.0.2`: connexion OK
- machine placable / utilisable
- recompenses delivrees sans erreur
- absence de duplication
- absence de crash

## Lot 10 - Cobblemon: Shiny Cookie

Statut:
- `deployed`
- `in_observation`

Perimetre retenu:
- serveur:
  - `Cobblemon: Shiny Cookie 0.0.1`
- client:
  - `Cobblemon: Shiny Cookie 0.0.1`

Preflight:
- script verifie:
  - `bash -n ./infra/mods-install-addon-lot10-shiny-cookie.sh`
- artefact verifie:
  - URL accessible
  - SHA256 conforme au verrou `0.0.1`

Execution:
- maintenance effectuee le `2026-03-07`
- script applique: `./infra/mods-install-addon-lot10-shiny-cookie.sh`
- checker cumulatif: `./infra/mods-check-addons-rollout.sh --through-lot 10`
- resultat checker final: `expected=35 ok=35 missing=0 hash_mismatch=0`

Incident corrige pendant maintenance:
- un premier check a ete lance trop tot (avant fin d'installation) et a affiche un `missing` transitoire
- le check a ete relance apres installation complete et est passe avec `missing=0`

Preuves operationnelles:
- backup pre-maintenance pris sur l'hote distant:
  - `backups/backup-20260307-115921.tar.gz`
- le serveur a redemarre correctement
- etat final apres redemarrage:
  - `status=running`
  - `health=healthy`
- annonce Discord de maintenance postee
- annonce Discord de reouverture postee
- message de reouverture envoye en jeu
- logs serveur coherents:
  - `shinycookie 0.0.1` present dans la liste des mods charges
  - `Done (5.534s)!`

Validation immediate:
- le lot est techniquement actif
- la fenetre d'observation `48h` est ouverte

Validation fonctionnelle attendue:
- client avec `Cobblemon: Shiny Cookie 0.0.1`: connexion OK
- obtention / utilisation controlee
- absence de crash
- absence d'effet anormal hors perimetre attendu

## Decision lot 11 - 2026-03-07

Decision:
- `Tomtaru's Cobblemon & Farmer's Delight Tweaks` reste bloque
- `Carry On` est retenu pour le lot `11`

Motif:
- `Tomtaru` ne propose pas de build Fabric 1.21.1 pour la stack actuelle
- `Carry On` propose une build Fabric 1.21.1 compatible

Communication:
- message Discord decisionnel publie:
  - Tomtaru bloque pour incompatibilite loader
  - lot 11 ouvert avec Carry On
  - actions annoncees: preparation + preflight + maintenance a planifier

## Lot 11 - Carry On

Statut:
- `deployed`
- `in_observation`

Perimetre retenu:
- serveur:
  - `Carry On 2.2.4.4`
- client:
  - `Carry On 2.2.4.4`

Preflight:
- script verifie:
  - `bash -n ./infra/mods-install-addon-lot11-carry-on.sh`
- artefact verifie:
  - URL accessible
  - SHA256 conforme au verrou `2.2.4.4`
- metadonnees verifiees:
  - `fabric.mod.json` declare `minecraft=1.21.1`
  - `fabric.mod.json` declare dependance `fabric-api`

Execution:
- maintenance effectuee le `2026-03-07`
- script applique: `./infra/mods-install-addon-lot11-carry-on.sh`
- checker cumulatif: `./infra/mods-check-addons-rollout.sh --through-lot 11`
- resultat checker final: `expected=36 ok=36 missing=0 hash_mismatch=0`

Incident corrige pendant maintenance:
- un premier check a ete lance en parallele de l'installation et a affiche un `missing` transitoire
- le check a ete relance apres installation complete et est passe avec `missing=0`

Preuves operationnelles:
- backup pre-maintenance pris sur l'hote distant:
  - `backups/backup-20260307-121636.tar.gz`
- le serveur a redemarre correctement
- etat final apres redemarrage:
  - `status=running`
  - `health=healthy`
- annonce Discord de maintenance postee
- annonce Discord de reouverture postee
- message de reouverture envoye en jeu
- logs serveur coherents:
  - `carryon 2.2.4` present dans la liste des mods charges
  - `Done (5.681s)!`

Validation immediate:
- le lot est techniquement actif
- la fenetre d'observation `48h` est ouverte

Validation fonctionnelle attendue:
- client avec `Carry On 2.2.4.4`: connexion OK
- prise/portage de blocs simple: OK
- prise/portage d'entites simple: OK
- pas de duplication
- pas de crash
