# Runbook: Politique De Restart

## Objectif
Eviter un restart brutal quand des joueurs sont connectes, tout en gardant un restart regulier.

## Script
- `infra/safe-restart.sh`
  - skip si joueurs online (sauf `--force`)
  - redemarre `cobblemon`
  - valide port `25565` + log `Done (...)`
  - alerte Discord via `MONITOR_WEBHOOK_URL` en cas d'echec

## Cron (recommande)
Exemple (restart quotidien, mais safe):
- `CRON_TZ=Europe/Paris`
- `0 5 * * * cd <MC_PROJECT_DIR> && <MC_PROJECT_DIR>/infra/safe-restart.sh --force >> <MC_PROJECT_DIR>/logs/minecraft-daily-restart.log 2>&1 # minecraft-daily-restart`

Avec `CRON_TZ=Europe/Paris`, le restart reste a `05:00` heure de Paris meme si le fuseau du serveur Linux est different.

Si tu preferes skip quand des joueurs sont connectes:
- remplacer `--force` par rien.
