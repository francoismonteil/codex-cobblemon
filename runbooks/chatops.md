# Runbook: ChatOps (admin via chat Minecraft)

## Objectif
Executer des actions d'admin (status, backup, restart) directement depuis le chat Minecraft, sans installer de plugin/mod ni exposer RCON.

Principe: un script sur le serveur surveille `./data/logs/latest.log`, detecte des messages `!mc <token> <commande>`, execute les scripts `infra/` et repond en message prive.

## Securite (important)
- Le script donne des pouvoirs "host admin". Ne l'active pas sans:
  - un `CHATOPS_TOKEN` fort (secret)
  - une allowlist stricte (`CHATOPS_ALLOW_PLAYERS`)
- Si ton serveur est en `online-mode=false`, un pseudo peut etre usurpe: dans ce cas, n'active pas ChatOps.

## Configuration
Dans `.env`:

```bash
CHATOPS_ENABLED=true
CHATOPS_LOG_FILE=./data/logs/latest.log
CHATOPS_PREFIX=!mc
CHATOPS_REQUIRE_TOKEN=true
CHATOPS_TOKEN=change-me
CHATOPS_ALLOW_PLAYERS=YourPlayerName
```

Option (moins safe): autoriser sans token (uniquement via allowlist de pseudos):

```bash
CHATOPS_REQUIRE_TOKEN=false
```

## Lancer le service
Sur le serveur Linux (dans le repo):

```bash
./infra/chatops.sh
```

Pour le laisser tourner: systemd / tmux / screen selon tes habitudes (non fourni par defaut).

## Commandes (in-game)
Dans le chat:

```text
!mc <token> help
!mc <token> status
!mc <token> backup
!mc <token> restart
```

Si `CHATOPS_REQUIRE_TOKEN=false`:

```text
!mc help
!mc status
!mc backup
!mc restart
```

Notes:
- Les reponses arrivent via `tell` (message prive) pour eviter le spam.
- `restart` fait un `save-all flush`, annonce un delai de 10s, puis lance `./infra/safe-restart.sh --force`.
