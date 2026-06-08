# Academy Dimension

Objectif: operer une dimension `acm_academy:academy` dans la meme instance serveur,
avec progression Academy globale et monde actuel conserve comme legacy.

## Decision gate

Le premier passage obligatoire reste:

```bash
./infra/academy-compat-audit.py
```

Tant que le rapport reste en `fidelity_reduced`, le serveur peut ouvrir:

- FTB Quests / Teams / Essentials / Library
- Numismatic Overhaul
- ExtraQuests
- RAD Gyms (+ RCT API + Admiral) apres staging
- dimension Academy et portail immersif

Mais il ne faut pas annoncer:

- vrai Safari Academy upstream
- houses Academy upstream
- acceptance letters / house pokedex upstream

## Install server stack

```bash
./infra/academy-stack-install.sh --all
./infra/safe-restart.sh --force
```

## Install dimension datapack

```bash
./infra/install-academy-dimension-datapack.sh --restart
```

Notes:

- la dimension est definie par datapack
- la world border vanilla reste globale au serveur
- l'exploitation utilise donc une `soft border Academy` geree par le datapack

## Bootstrap portals

```bash
./infra/spawn-academy-portals.sh
```

Variables utiles:

- `OVERWORLD_OFFSET_X`
- `OVERWORLD_OFFSET_Z`
- `OVERWORLD_Y`
- `ACA_PORTAL_X`
- `ACA_PORTAL_Y`
- `ACA_PORTAL_Z`
- `ACA_ARRIVAL_X`
- `ACA_ARRIVAL_Y`
- `ACA_ARRIVAL_Z`

## Staging checklist

1. Installer le nouveau profil client Academy V2 sur un client propre
2. Rejoindre le serveur sans mismatch
3. Attendre le chargement complet de la dimension Academy
4. Utiliser le portail overworld -> Academy
5. Verifier le cooldown anti-boucle au retour
6. Relancer le serveur et revalider la connexion d'un joueur stationne en Academy
7. Installer ensuite les quetes/configs FTB et l'economie Numismatic
8. Installer enfin RAD Gyms et refaire un cycle complet de persistance

## Pregen

Le datapack cree la dimension, mais la pre-generation reste une etape operateur separee.
Avant annonce publique:

1. redemarrer le serveur
2. charger la dimension Academy une premiere fois
3. lancer la pregen de la zone retenue avec votre procedure Chunky habituelle
4. ne pas ouvrir la dimension au public avant la fin de la pregen

## Rollback

Cas de rollback immediat:

- crash de connexion apres ajout de la stack Academy
- corruption de progression FTB
- corruption Numismatic
- boucles de teleportation
- joueur perdu ou invalide au redemarrage en Academy

Actions:

1. `./infra/stop.sh`
2. restaurer le dernier backup sain via `./infra/restore.sh`
3. retirer les mods Academy ajoutes dans `./data/mods`
4. supprimer ou restaurer le datapack `./data/world/datapacks/acm_academy_dimension`
5. redemarrer
