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
- `python3 ./infra/pokedex-report.py`
- `./infra/mc.sh`, `./infra/player.sh`, `./infra/onboard.sh`, `./infra/kickoff.sh`, `./infra/item.sh`
- `./infra/friend-info.sh`, `./infra/player-check.sh`, `./infra/ops-list.sh`
- `./infra/friend-info-webhook.sh`
- `./infra/discord-bot.sh`, `./infra/discord_whitelist_bot.py`

## Core ops (`utility`)
- `./infra/starter.sh` (kit de depart donne a un joueur)
- `./infra/command-blocks.sh` (active/desactive les command blocks avec restart)

## Open world (`entrypoint`)
- `./infra/openworld-village-init.sh`
- `./infra/openworld-village-init-until-pokemart.sh`
- `./infra/openworld-border-extend.sh`
- `./infra/server-profile-openworld-4p.sh`
- `./infra/install-pokemon-worldgen-datapack.sh`
- `./infra/detect-pokemart-near-spawn.py`
- `./infra/prepare-additionalstructures-1211.sh`
- `./infra/install-additionalstructures-datapack.sh`
- `./infra/validate-worldgen-datapacks.sh`
- `./infra/chunky-monitor-enable-cron.sh`, `./infra/chunky-monitor-disable-cron.sh`

## Open world (`utility`)
- `./infra/openworld-village-configure.sh` (configure un monde deja genere)
- `./infra/world-trim-around-spawn.sh` (conserve un carre autour du spawn, purge hors zone)
- `./infra/mods-install-openworld.sh`
- `./infra/flan-configure-claim-tools.sh`
- `./infra/mods-install-waystones.sh`
- `./infra/mods-install-better-qol.sh`
- `./infra/mods-install-storage.sh`
- `./infra/mods-check-recommended.sh`
- `./infra/waystones-backfill-villages.py` (scan villages generes + placement Waystones par batch avec journal `--resume`)
- `./infra/chunky-monitor.sh` (supervision ponctuelle Chunky en direct)
- `./infra/spawn-village-pokecenter-auto.sh` (manuel, hors demarrage)
- `./infra/spawn-village-pokecenter-decorate.sh` (manuel, hors demarrage)
- `./infra/spawn-village-welcome-cache.sh` (manuel, hors demarrage)
- `./infra/spawn-village-upgrade.sh` (manuel, hors demarrage)
- `./infra/spawn-poke-kit.sh` (manuel, hors demarrage)
- `./infra/spawn-pokecenter-prefab.sh`
- `./infra/hostile-mob-tower-auto.sh` (pipeline auto ferme XP hostile + rollback)
- `./infra/spawn-hostile-mob-tower.sh` (build manuel/absolu)
- `./infra/clear-hostile-mob-tower.sh` (cleanup cible)
- `./infra/find-hostile-mob-tower-site.py` (choix de site)
- `./infra/validate-hostile-mob-tower.py` (validation post-build)
- `./infra/spawn-village-house-upgrade-auto.sh`

Runbook associe (mods recommandes):
- `runbooks/server-mods-recommended-install.md`

Runbook associe (Waystones sur map existante):
- `runbooks/waystones-backfill-existing-villages.md`

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
- `./infra/world_tools.py`
- `./infra/hostile_mob_tower_spec.py`

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
- `./infra/deploy-server.ps1` (sync workspace -> serveur sans git sur la cible; options `-DryRun`, `-NoDeleteExtra`, `-CreateRemoteBackup`, `-VerifyService`)
