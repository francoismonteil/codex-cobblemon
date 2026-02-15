# Runbook: Alerting (Discord webhook)

## Objectif
Recevoir une alerte si:
- le conteneur `cobblemon` n'est plus `running/healthy`
- le port `25565` n'ecoute plus
- disque/RAM/load depassent les seuils

## 1) Creer un webhook Discord
Dans Discord (serveur -> salon -> Parametres du salon -> Integrations -> Webhooks):
1. Creer un webhook.
2. Copier l'URL du webhook.

## 2) Configurer le serveur
Sur `<MC_SSH_USER>@<MC_SERVER_HOST>`, dans `<MC_PROJECT_DIR>/.env`:
- `MONITOR_WEBHOOK_URL=https://discord.com/api/webhooks/...`

## 3) Tester
Depuis `<MC_PROJECT_DIR>`:

```bash
./infra/webhook-test.sh
```

Si c'est OK, tu dois voir un message "TEST ..." dans Discord.

## Notes
- Le monitor est deja lance via cron `minecraft-monitor` (voir `runbooks/ops-notes.md`).
- Seuils dans `.env`:
  - `MONITOR_DISK_MAX_PCT`
  - `MONITOR_MEM_MAX_PCT`
  - `MONITOR_LOAD1_MAX`
  - `MONITOR_CONTAINER_MEM_MAX_PCT`
