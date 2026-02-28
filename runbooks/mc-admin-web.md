# Runbook: Admin web Minecraft (prive, sans RCON)

## Objectif
Exposer un petit panneau web prive pour administrer le serveur Minecraft sans ouvrir RCON.

## Perimetre MVP
- statut du conteneur `cobblemon`
- start / stop / restart
- lecture des logs
- backup
- whitelist / op / deop
- onboarding joueur

## Prerequis
- Docker et Docker Compose fonctionnels sur l'hote Linux
- `CREATE_CONSOLE_IN_PIPE=true` pour les actions qui passent par `infra/mc.sh`
- acces prive uniquement: tunnel SSH ou VPN
- variables `MC_ADMIN_WEB_*` renseignees dans `.env`

## Variables `.env`
```bash
MC_ADMIN_WEB_PORT=8080
MC_ADMIN_WEB_PASSWORD=<mot-de-passe-long-et-unique>
MC_ADMIN_WEB_SESSION_SECRET=<secret-long-et-aleatoire>
MC_ADMIN_WEB_COOKIE_SECURE=false
MC_ADMIN_WEB_JOB_HISTORY=100
```

Notes:
- laisse `MC_ADMIN_WEB_COOKIE_SECURE=false` si tu passes par un tunnel SSH HTTP local
- passe a `true` uniquement si le panneau est servi derriere HTTPS

## Demarrage
Sur le serveur Linux, dans `<MC_PROJECT_DIR>`:

```bash
docker compose up -d mc-admin-web
```

Pour rebuild apres modification du code:

```bash
docker compose build mc-admin-web
docker compose up -d mc-admin-web
```

## Acces via tunnel SSH
Depuis ta machine admin:

```bash
ssh -L 8080:127.0.0.1:8080 -i <SSH_KEY_MAIN> <MC_SSH_USER>@<MC_SERVER_HOST>
```

Puis ouvre:

```text
http://127.0.0.1:8080
```

## Actions supportees
- `Start`: demarre uniquement le conteneur `cobblemon`
- `Stop`: arrete uniquement le conteneur `cobblemon`
- `Restart`: restart du conteneur puis attente d'un etat `healthy` ou `none`
- `Backup`: appelle `./infra/backup.sh`
- `Whitelist / OP / Deop / Onboard`: wrappers autour de `./infra/player.sh` et `./infra/onboard.sh`

## Securite
- ne pas exposer ce panneau directement sur Internet dans ce MVP
- le conteneur monte `/var/run/docker.sock`: cela donne des privileges eleves sur l'hote
- ne pas reutiliser un mot de passe faible ou partage
- l'app n'accepte pas de console libre; seules les actions allowlistees sont disponibles

## Depannage
### Le login ne marche pas
- verifier `MC_ADMIN_WEB_PASSWORD` dans `.env`
- redemarrer le service apres changement:

```bash
docker compose up -d mc-admin-web
```

### Le panneau repond mais les actions echouent
- verifier que `cobblemon` existe encore:

```bash
docker ps -a --filter name=cobblemon
```

- verifier que le socket Docker est bien monte dans `mc-admin-web`
- verifier que `CREATE_CONSOLE_IN_PIPE=true` est toujours actif

### Les actions whitelist/onboard echouent
Ces actions utilisent `infra/mc.sh`. Si la console pipe n'est pas disponible, elles ne marcheront pas.

### Le panneau ne demarre pas
Consulter les logs:

```bash
docker compose logs --tail=200 mc-admin-web
```

## Arret rapide
```bash
docker compose stop mc-admin-web
```
