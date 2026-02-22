# Runbook: Admin Minecraft (sans RCON)

## Objectif
Executer des commandes d'admin (gamemode, whitelist, op, etc.) rapidement sans exposer RCON.

## Prerequis
- Le conteneur doit avoir `CREATE_CONSOLE_IN_PIPE=true`.
- Le script `infra/mc.sh` doit etre present et executable.

## Commandes courantes
Sur le serveur, dans `<MC_PROJECT_DIR>`:

```bash
./infra/mc.sh list
./infra/mc.sh "gamemode creative <player>"
./infra/mc.sh "gamemode survival <player>"
./infra/mc.sh "effect give <player> minecraft:resistance 999999 255 true"
./infra/item.sh cobblestone 64
./infra/item.sh minecraft:diamond 3 <player>
./infra/mc.sh "whitelist add <Pseudo>"
./infra/mc.sh "whitelist remove <Pseudo>"
./infra/mc.sh "op <Pseudo>"
./infra/mc.sh "deop <Pseudo>"
```

## Onboarding rapide d'un ami (1 commande)

```bash
./infra/player.sh add <Pseudo>
./infra/player.sh add <Pseudo> --op
./infra/player.sh remove <Pseudo>
./infra/player.sh list
./infra/player-check.sh <Pseudo>
./infra/ops-list.sh
./infra/friend-info-webhook.sh

./infra/onboard.sh <Pseudo>
./infra/onboard.sh <Pseudo> --op
./infra/kickoff.sh <Pseudo>
```

## Notes
- "God mode" vanilla n'existe pas en commande unique. Le plus proche, c'est:
  - `gamemode creative <Pseudo>` (recommande)
  - ou des effets (resistance/regen), mais c'est moins propre.
