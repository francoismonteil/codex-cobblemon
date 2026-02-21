# Infra Commands Index

Objectif: index rapide des scripts `infra/` et de leur statut d'usage.

Convention:
- `entrypoint`: commande operatoire recommandee pour exploitation quotidienne.
- `utility`: outil ponctuel utile selon contexte.
- `internal`: script de support/engineering (pas un flux runbook principal).
- `legacy`: conserve pour historique ou migration.

## Core ops (`entrypoint`)
- `./infra/start.sh`, `./infra/stop.sh`, `./infra/logs.sh`, `./infra/status.sh`
- `./infra/backup.sh`, `./infra/restore.sh`, `./infra/safe-restart.sh`
- `./infra/monitor.sh`, `./infra/webhook-test.sh`
- `./infra/mc.sh`, `./infra/player.sh`, `./infra/onboard.sh`, `./infra/kickoff.sh`, `./infra/item.sh`

## Core ops (`utility`)
- `./infra/starter.sh` (kit de depart donne a un joueur)
- `./infra/command-blocks.sh` (active/desactive les command blocks avec restart)

## Open world (`entrypoint`)
- `./infra/openworld-village-init.sh`
- `./infra/openworld-border-extend.sh`
- `./infra/server-profile-openworld-4p.sh`
- `./infra/install-pokemon-worldgen-datapack.sh`
- `./infra/prepare-additionalstructures-1211.sh`
- `./infra/install-additionalstructures-datapack.sh`
- `./infra/validate-worldgen-datapacks.sh`
- `./infra/chunky-monitor-enable-cron.sh`, `./infra/chunky-monitor-disable-cron.sh`

## Open world (`utility`)
- `./infra/openworld-village-configure.sh` (configure un monde deja genere)
- `./infra/mods-install-openworld.sh`
- `./infra/chunky-monitor.sh` (supervision ponctuelle Chunky en direct)
- `./infra/spawn-village-pokecenter-auto.sh`
- `./infra/spawn-village-pokecenter-decorate.sh`
- `./infra/spawn-village-welcome-cache.sh`
- `./infra/spawn-village-upgrade.sh`
- `./infra/spawn-poke-kit.sh`
- `./infra/spawn-pokecenter-prefab.sh`
- `./infra/spawn-village-house-upgrade-auto.sh`

## Worlds / maps (`entrypoint`)
- `./infra/world-import-zip.sh`
- `./infra/worlds-list.sh`
- `./infra/world-switch.sh`

## Worlds / maps (`utility`)
- `./infra/world-install-from-zip.sh`
- `./infra/world-install-cobblemon-johto.sh`
- `./infra/world-spawn.sh`

## Progression / gameplay (`entrypoint`)
- `./infra/progression-init.sh`
- `./infra/badge.sh`

## ChatOps / network / backups (`entrypoint`)
- `./infra/chatops.sh`
- `./infra/ddns-duckdns.sh`
- `./infra/backup-secondary.sh`

## Johto FR (`utility`)
- `./infra/johto-fr-generate.sh`
- `./infra/johto-fr-install.sh`
- `./infra/johto-fixpack-generate.sh`

## Build / templates (`internal`)
- `./infra/prefab-lib.sh`, `./infra/prefab-score.sh`, `./infra/prefab-score.py`
- `./infra/pokecenter-template-capture.sh`
- `./infra/pokecenter-prefab-stash.sh`, `./infra/pokecenter-prefab-restore.sh`
- `./infra/spawn-schematic-mcedit.sh`
- `./infra/schematic-mcedit-to-commands.py`
- `./infra/schematic-mcedit-to-structure-nbt.py`
- `./infra/build-modern-spawn.sh`
- `./infra/build-windmill-structure.sh`
- `./infra/world-height-at.py`

## Legacy
- `./infra/install-village-pokecenter-datapack.sh`
- `./infra/install-windmill-datapack.sh`
- `./infra/spawn-city.sh`
- `./infra/spawn-gym.sh`
- `./infra/spawn-shop.sh`
- `./infra/spawn-signage.sh`
- `./infra/spawn-windmill.sh`
- `./infra/spawn-windmill-template.sh`
- `./infra/spawn-windmills-plains.sh`
- `./infra/new-world-and-spawn.sh`
- `./infra/pve-chill.sh`
- `./infra/datapacks-prune-prev.sh`

## Windows wrappers
- `./infra/start.ps1`, `./infra/stop.ps1`, `./infra/logs.ps1`
- `./infra/backup.ps1`, `./infra/restore.ps1`
