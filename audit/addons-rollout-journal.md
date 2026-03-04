# Addons rollout journal

Objectif:
- consigner l'execution reelle des lots addons Cobblemon
- garder une trace courte des validations, backups, checks et suites

Base cible:
- Minecraft `1.21.1`
- Loader `Fabric`
- Cobblemon `1.7.3`

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
