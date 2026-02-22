# Runbook: Friends Guide (connexion + whitelist)

## Objectif
Donner a des amis (ou a un co-admin) un moyen simple de retrouver:
- les infos de connexion
- la version client/modpack a installer
- le statut whitelist/op (sans bricoler dans les logs)

## Ce qui est partageable / non partageable
- Partageable: adresse de jeu, port, version Minecraft, modpack exact, procedure d'installation.
- A garder prive: SSH, cles, tokens ChatOps, contenu de `runbooks/site.local.md`.
- `ops list`: reservee aux admins/co-admins de confiance.

## Commandes utiles (serveur / SSH)

### Infos de connexion a copier-coller

```bash
./infra/friend-info.sh
./infra/friend-info.sh --markdown
./infra/friend-info-webhook.sh
```

Le script lit `.env` (ex: `DUCKDNS_DOMAINS`) et affiche:
- adresse serveur
- version Minecraft attendue
- modpack exact
- rappel anti "Version mismatch"

Pour publier directement sur Discord (webhook):
- configure `FRIENDS_WEBHOOK_URL` (ou reutilise `MONITOR_WEBHOOK_URL`)
- lance `./infra/friend-info-webhook.sh`
- test local sans envoi: `./infra/friend-info-webhook.sh --dry-run`

### Verifier whitelist / op d'un pseudo

```bash
./infra/player-check.sh <Pseudo>
./infra/player-check.sh --json <Pseudo>
```

Sortie attendue:
- `Whitelist: yes/no`
- `Op: yes/no`

### Lister la whitelist (offline, depuis le fichier)

```bash
./infra/player.sh list
```

### Lister les ops (admin only)

```bash
./infra/ops-list.sh
./infra/ops-list.sh --full
```

## Ajouter / retirer un joueur (co-admin)

```bash
./infra/onboard.sh <Pseudo>
./infra/onboard.sh <Pseudo> --op
./infra/player.sh remove <Pseudo>
```

## Guide client a partager aux amis
- Reference detaillee: `runbooks/client-setup.md`
- Version actuelle (par defaut): Minecraft `1.21.1`
- Modpack: `Cobblemon Official Modpack [Fabric] 1.7.3`

## Conseils d'usage "quand je ne suis pas la"
- Partage `runbooks/friends-guide.md` + la sortie de `./infra/friend-info.sh` dans un salon Discord epingle.
- Donne l'acces SSH seulement a un co-admin de confiance si tu veux qu'il gere whitelist/op.
- N'expose pas `ops list` publiquement aux joueurs.
