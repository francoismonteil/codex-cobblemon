# Infra Cobblemon (Docker)

## Demarrage (Windows / PowerShell)

```powershell
cp .env.example .env
./infra/start.ps1
```

## Arret (Windows / PowerShell)

```powershell
./infra/stop.ps1
```

## Logs (Windows / PowerShell)

```powershell
./infra/logs.ps1
```

## Administration via SSH (Linux)

Depuis ta machine:

```bash
ssh <user>@<server-ip>
cd /opt/codex-cobblemon
cp -n .env.example .env
./infra/start.sh
```

Commandes utiles sur le serveur:

```bash
./infra/logs.sh
./infra/backup.sh
./infra/restore.sh backups/backup-YYYYMMDD-HHMMSS.tar.gz
./infra/stop.sh
./infra/monitor.sh
```

## Admin depuis le chat (ChatOps, sans plugin/mod)

Option: activer un petit "ChatOps" qui ecoute le chat Minecraft via `./data/logs/latest.log` et declenche des actions admin.

Runbook: `runbooks/chatops.md`

Lancement (Linux):

```bash
./infra/chatops.sh
```

## Bot Discord (whitelist self-service)

Option: utiliser un bot Discord (slash commands) pour permettre a des amis/co-admins d'ajouter un pseudo a la whitelist sans SSH.

Runbook: `runbooks/discord-bot.md`

Installation / lancement (Linux):

```bash
./infra/discord-bot.sh check-env
./infra/discord-bot.sh install
./infra/discord-bot.sh run
```

## Monitoring leger

Le script `./infra/monitor.sh` verifie:
- statut/health du conteneur `cobblemon`
- port `25565` en ecoute
- pression disque, RAM hote, load average
- pression memoire du conteneur

Variables `.env`:
- `TZ` (defaut `Europe/Paris`)
- `EULA` (defaut `TRUE`)
- `TYPE` (defaut `MODRINTH`)
- `MODRINTH_MODPACK` (defaut `cobblemon-fabric`)
- `MODRINTH_VERSION` (defaut `Lydu1ZNo`)
- `MEMORY` (defaut `4608M`)
- `USE_AIKAR_FLAGS` (defaut `true`)
- `MONITOR_WEBHOOK_URL` (optionnel)
- `DUCKDNS_DOMAINS` (optionnel, pour DDNS)
- `DUCKDNS_TOKEN` (optionnel, pour DDNS)
- `SECONDARY_BACKUP_DIR` (optionnel, copie backup sur 2e disque)
- `SECONDARY_BACKUP_KEEP` (defaut `30`, nombre d'archives a conserver sur le 2e disque)
- `MONITOR_DISK_MAX_PCT` (defaut `85`)
- `MONITOR_MEM_MAX_PCT` (defaut `92`)
- `MONITOR_LOAD1_MAX` (defaut `6`)
- `MONITOR_CONTAINER_MEM_MAX_PCT` (defaut `95`)

Logs:
- metriques: `./logs/minecraft-monitor.log`

## Donnees et backups

- Donnees serveur: `./data` (monte sur `/data` dans le conteneur)
- Backups: `./backups` (monte sur `/backups` dans le conteneur)
- Modpack: telecharge automatiquement via Modrinth (TYPE=MODRINTH) avec la version pinnee `Lydu1ZNo`. Les fichiers finissent dans `./data` (ex: `./data/modpack`).
- Monde: `./data/world`

## Pre-generation (Chunky, mode modere)
Option: utiliser `docker-compose.pregen.yml` uniquement pendant la pre-generation pour limiter l'usage CPU (ex: 2 coeurs).

## Scripts existants

- Windows PowerShell: `./infra/start.ps1`, `./infra/stop.ps1`, `./infra/logs.ps1`, `./infra/backup.ps1`, `./infra/restore.ps1`
- Linux Bash: `./infra/start.sh`, `./infra/stop.sh`, `./infra/logs.sh`, `./infra/backup.sh`, `./infra/restore.sh`

Progression:
- `./infra/progression-init.sh`: initialise les scoreboards de badges
- `./infra/badge.sh`: attribue / consulte les badges d'un joueur

Settings:
- `./infra/command-blocks.sh`: active/desactive les command blocks (avec restart)

Monde (import map):
- `./infra/world-install-cobblemon-johto.sh`: installe la map "Cobblemon Johto" (CurseForge) dans `./data/world`
- `./infra/world-install-from-zip.sh`: installe un monde depuis une archive zip dans `./data/world`
- `./infra/world-import-zip.sh`: importe un monde zip dans la bibliotheque `./worlds/<name>` (sans toucher le monde actif)
- `./infra/world-switch.sh`: active un monde depuis `./worlds/<name>` (stop/start et backup du monde actif)
- `./infra/worlds-list.sh`: liste les mondes disponibles dans `./worlds`
- `./infra/world-spawn.sh`: lit le spawn du monde (level.dat) pour l'onboarding

Monde (open world):
- `./infra/server-profile-openworld-4p.sh`: applique un profil serveur (PvP off, whitelist on, 4 joueurs, distances).
- `./infra/mods-install-openworld.sh`: installe les mods serveur utilitaires (Chunky + Flan) requis pour l'open world.
- `./infra/mods-install-waystones.sh`: installe `Waystones` + dependance `Balm` (mods gameplay, clients requis aussi), versions pinnees pour Fabric 1.21.1.
- `./infra/mods-install-better-qol.sh`: installe le pack QoL serveur "Better Minecraft-like" retenu (`spark`, `Traveler's Backpack`, `FallingTree`, `YIGD` + dependance `Cardinal Components API`), versions pinnees pour Fabric 1.21.1.
- `./infra/mods-install-storage.sh`: installe les mods de stockage gameplay (`Storage Drawers`, `Tom's Simple Storage Mod`), versions pinnees pour Fabric 1.21.1.
- `./infra/mods-check-recommended.sh`: verifie `./data/mods` contre le pack serveur recommande (fichiers manquants, hash mismatch, extras) et ecrit `audit/recommended-server-mods-check.json`.
- `./infra/waystones-backfill-villages.py`: detecte les villages deja generes (scan `.mca`) et pose des `Waystones` par batch via `./infra/mc.sh` avec journal `--resume` (map existante).
- `./infra/openworld-village-init.sh`: nouveau monde open world (spawn village naturel + border 4000 + protection spawn + pregen), **sans poser automatiquement healer/PC**.
- `./infra/openworld-village-init-until-pokemart.sh`: relance l'init open world jusqu'a obtenir un nombre de clusters Pokemart acceptable pres du spawn (defaut: exactement 1, via `--min-components 1 --max-components 1`).
- `./infra/openworld-border-extend.sh`: extension de border + reprise pregen.
- `./infra/prefab-score.sh`: calcule un score de qualite d'une structure (jouabilite + esthetique) en lisant les blocs + lumiere depuis le monde sur disque (bbox ou 4 coins).
- `./infra/spawn-poke-kit.sh`: pose un healer + PC Cobblemon a des coordonnees (sans construire un batiment), **en manuel post-demarrage**.
- `./infra/spawn-village-pokecenter-auto.sh`: pose automatiquement un healer + PC pres du centre du village (meilleur effort, sans coords manuelles), **en manuel post-demarrage**.
- `./infra/spawn-village-pokecenter-decorate.sh`: ajoute un habillage subtil autour du kit (carpets + utilitaires), sans overwrite, **en manuel post-demarrage**.
- `./infra/spawn-village-welcome-cache.sh`: place/stocke un petit baril de bienvenue pres du kit (pain, torches, lits, pokeballs), **en manuel post-demarrage**.
- `./infra/spawn-pokecenter-prefab.sh`: construit un petit prefab "Centre Pokemon" (basic ou decorated) dans un rectangle (4 coins).
- `./infra/spawn-village-upgrade.sh`: upgrade leger d'une maison de village (healer+PC + accents + blocs utiles).
- `./infra/install-pokemon-worldgen-datapack.sh`: installe/met a jour le datapack `acm_pokemon_worldgen` dans le monde actif.
- `./infra/detect-pokemart-near-spawn.py`: detecte des marqueurs Pokemart dans les chunks proches du spawn et calcule le nombre de clusters connectes (lecture monde sur disque).
- `./infra/prepare-additionalstructures-1211.sh`: normalise AS pour 1.21.1 et applique le gate compatibilite.
- `./infra/install-additionalstructures-datapack.sh`: installe/met a jour le datapack `additionalstructures_1211` dans le monde actif (flux nouveau monde).
- `./infra/validate-worldgen-datapacks.sh`: validation stricte ACM+AS (statique + logs startup).
- `./infra/chunky-monitor.sh`: supervision Chunky (log + webhook Discord si configure).
- `./infra/chunky-monitor-enable-cron.sh`: active la supervision en arriere-plan via cron.
- `./infra/chunky-monitor-disable-cron.sh`: desactive la supervision en arriere-plan via cron.

## Prefab Score

Le script `./infra/prefab-score.sh` (wrapper) appelle `./infra/prefab-score.py` pour scorer une structure via la lecture du monde sur disque.

## Navigation scoring

Flags principaux:
- `--nav-start-mode door_cell|inside_cell|both` (defaut: `inside_cell`)
- `--doors-passable true|false` (defaut: `true`)
- `--trapdoors-passable true|false` (defaut: `true`)

Definition des modes de depart:
- `door_cell`: depart sur la cellule de porte (peut etre bloquant si `--doors-passable=false`).
- `inside_cell`: depart sur la cellule juste derriere la porte (recommande, plus interpretable).
- `both`: union des deux.

Conventions coordonnees / `--facing`:
- Minecraft: `north` = Z-1, `south` = Z+1, `east` = X+1, `west` = X-1.
- Ici `--facing` = direction de la facade / vers l'exterieur.
- Le "dedans" (`inside_cell`) est calcule en prenant l'oppose de `--facing` et en avancant d'1 bloc depuis la porte.

Definition de `reachable_ratio`:
- Le ratio est calcule sur une "zone d'interet" stable: le plan `y_walk` a l'interieur de la bbox en ignorant un anneau de 1 bloc sur le pourtour.
- Objectif: si la bbox inclut 1 bloc d'exterieur par erreur, le score navigation ne s'effondre pas.
- Cas particulier: si la bbox est trop petite, l'outil repasse en mode `bbox` (voir `metrics.walk.denominator` et `metrics.walk.interest_box`).
- Dans le JSON, les champs suffixes `*_bbox` sont les metriques brutes sur la bbox complete; les champs sans suffixe sont sur `interest_box`.

Audit portes:
- `doors_detected` = toutes les portes (blocs `*_door`) dans le volume.
- `doors_found` = portes detectees pres de la facade (cellules X/Z, depend de `--facing`).

Audit lumiere (spawn):
- `spawn_check_applicable` = il existe au moins une position spawnable (air+air au-dessus d'une surface spawnable) dans l'interieur accessible.
- `light_eval_positions` = nombre de positions spawnables evaluees pour la lumiere (== `spawnable_positions`).
- `light_data_reliable` = vrai seulement si `spawn_check_applicable=true` ET 0 position avec lumiere inconnue.
- `light_data_coverage` = fraction des positions spawnables avec lumiere connue (utile pour voir un "partiellement fiable").
