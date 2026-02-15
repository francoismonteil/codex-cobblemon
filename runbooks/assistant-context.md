# Assistant Context

Last updated: 2026-02-12

## Defaults
- This repo is meant to be shareable (no personal IPs/paths in git).
- Put real values in `runbooks/site.local.md` (gitignored). Template: `runbooks/site.local.md.example`.

Defaults (placeholders):
- "server" = remote Minecraft host `<MC_SERVER_HOST>`
- SSH user: `<MC_SSH_USER>`
- Project path on server: `<MC_PROJECT_DIR>` (example: `/home/linux/codex-cobblemon`)
- Minecraft service/container name: `<MC_SERVICE_NAME>` (example: `cobblemon`)
- Game port: `<MC_PORT>/tcp` (example: `25565/tcp`)
- Default player name (when you say "me"): `<DEFAULT_PLAYER_NAME>`
  - Also stored in `.env` as `DEFAULT_PLAYER_NAME` (local/server, not committed)

## SSH commands
- Main key:
  `ssh -i <SSH_KEY_MAIN> <MC_SSH_USER>@<MC_SERVER_HOST>`
- Emergency key:
  `ssh -i <SSH_KEY_EMERGENCY> <MC_SSH_USER>@<MC_SERVER_HOST>`

## Short aliases (conversation)
- `mc status` = check service/container state + port 25565
- `mc start` = start minecraft service
- `mc stop` = stop minecraft service
- `mc logs` = show minecraft logs
- `mc cmd <...>` = send a server console command (uses `infra/mc.sh`, no RCON)

## Canonical references
- Operational notes: `runbooks/ops-notes.md`
- Infra scripts: `infra/*.sh`, `infra/*.ps1`
