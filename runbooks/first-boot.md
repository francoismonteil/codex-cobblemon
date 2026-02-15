# Runbook: Premier demarrage (Cobblemon)

## Preconditions
- `docker compose` disponible sur l'hote.
- Fichiers config presents: `.env`, `docker-compose.yml`.
- Volumes locaux accessibles: `./data`, `./backups`.

## Procedure
1) Demarrer la stack:
```bash
docker compose up -d
```
2) Suivre les logs:
```bash
docker compose logs -f --tail=200
```
3) Attendre un indicateur de demarrage:
- `Done (X.XXXs)! For help, type "help"`
- `Starting minecraft server version ...`
4) Verifier les repertoires generes dans `./data` (`world`, `logs`, `config`, ...).

## Criteres OK
- Le conteneur reste `Up` apres 2+ minutes.
- Pas d'erreurs recurrentes apres la ligne `Done`.
- Le port `25565` est expose.

## En cas d'echec
- Suivre `runbooks/crash-startup.md`.
