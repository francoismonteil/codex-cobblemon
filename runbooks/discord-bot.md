# Runbook: Discord Bot (whitelist self-service)

## Objectif
Permettre a des amis (ou co-admins) de gerer la whitelist depuis Discord, sans acces SSH.

Le bot execute localement les scripts existants du repo:
- `./infra/friend-info.sh`
- `./infra/player-check.sh`
- `./infra/onboard.sh`
- `./infra/starter.sh` (drain automatique du starter en attente a la connexion)

## Securite (important)
- Utiliser un bot Discord dedie (token prive).
- Restreindre le bot a un serveur (`DISCORD_BOT_GUILD_ID`).
- Restreindre a un salon et/ou a un role (`DISCORD_BOT_ALLOWED_CHANNEL_IDS`, `DISCORD_BOT_ALLOWED_ROLE_IDS`).
- Le bot **n'ajoute pas d'op**. Il ajoute seulement a la whitelist via `onboard.sh`.

## Variables `.env`

Ajouter (exemple):

```bash
DISCORD_BOT_TOKEN=
DISCORD_BOT_GUILD_ID=123456789012345678
DISCORD_BOT_ALLOWED_CHANNEL_IDS=123456789012345678
DISCORD_BOT_ALLOWED_ROLE_IDS=123456789012345678
DISCORD_BOT_COMMAND_TIMEOUT_SEC=20
DISCORD_BOT_STARTER_WATCH_ENABLED=true
```

Notes:
- `DISCORD_BOT_GUILD_ID` est recommande (sync rapide des slash commands).
- Si `DISCORD_BOT_ALLOWED_ROLE_IDS` est vide, tout membre du serveur/salon autorise pourra lancer `/mc whitelist`.

## Installation (serveur Linux)

Depuis le repo:

```bash
./infra/discord-bot.sh check-env
./infra/discord-bot.sh install
```

Prerequis:
- `python3`
- `python3-venv`
- acces reseau sortant vers Discord

## Lancement

```bash
./infra/discord-bot.sh run
```

Le bot reste au premier plan. Utiliser `tmux`, `screen` ou un service systemd pour le laisser tourner.

## Commandes Discord (slash)

- `/mc info` : affiche les infos de connexion et d'installation client
- `/mc check pseudo:<Pseudo>` : verifie whitelist / op
- `/mc whitelist pseudo:<Pseudo>` : ajoute a la whitelist (via `onboard.sh`)
  - si le joueur est offline, le starter kit est mis en attente puis distribue automatiquement a sa premiere connexion (lecture de `data/logs/latest.log`)
- `/mc starter pseudo:<Pseudo>` : donne le starter maintenant si le joueur est en ligne, sinon le met en attente

## Debogage rapide
- Verifier `.env`: `./infra/discord-bot.sh check-env`
- Verifier scripts locaux:
  - `./infra/friend-info.sh`
  - `./infra/player-check.sh --json <Pseudo>`
  - `./infra/onboard.sh <Pseudo>`
- Si les slash commands n'apparaissent pas:
  - verifier que `DISCORD_BOT_GUILD_ID` est correct
  - relancer le bot
  - verifier les scopes d'invitation du bot (`bot` + `applications.commands`)
