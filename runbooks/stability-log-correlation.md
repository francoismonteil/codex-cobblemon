# Runbook: Correlation logs client / serveur

Objectif:
- corréler les sessions client locales avec les événements serveur distants
- distinguer `client-only`, `serveur-only` et `corrélé`
- produire rapidement un audit de stabilité exploitable

## Référence horaire
- Utiliser l'horloge du conteneur Minecraft, pas celle de l'hôte SSH.
- Vérification:
```bash
docker exec cobblemon date --iso-8601=seconds
```
- Règle:
  - si les timestamps conteneur et client sont alignés, corréler directement à la seconde
  - sinon, mesurer l'écart puis translater toutes les recherches serveur de cet offset avant d'interpréter

## Collecte rapide

### Client local
```bash
py -3 tools/stability_audit.py --start-date 2026-03-04 --end-date 2026-03-08
```

### Serveur distant
La collecte distante passe par `runbooks/site.local.md`:
- `MC_SERVER_HOST`
- `MC_SSH_USER`
- `MC_PROJECT_DIR`
- `SSH_KEY_MAIN`

Commandes utiles en direct:
```bash
ssh -i <SSH_KEY_MAIN> <MC_SSH_USER>@<MC_SERVER_HOST> "cd <MC_PROJECT_DIR> && docker compose logs --tail=200 cobblemon"
ssh -i <SSH_KEY_MAIN> <MC_SSH_USER>@<MC_SERVER_HOST> "cd <MC_PROJECT_DIR> && zgrep -En \"Can't keep up|Exception|ERROR|lost connection|Server closed|Unable to close Phantom Array|Generation for section .* expired\" data/logs/2026-03-08-*.log.gz"
```

## Outil recommandé
```bash
py -3 tools/stability_audit.py --start-date 2026-03-04 --end-date 2026-03-08 --write
```

Sortie:
- `audit/stability-audit-20260308.json`

## Synthese journaliere serveur
Pour le suivi quotidien hors corrélation client:
```bash
py -3 tools/server_log_digest.py --start-date 2026-03-10 --end-date 2026-03-10 --write
```

Sorties:
- `audit/server-log-digest-YYYYMMDD.json`
- `audit/server-log-digest-YYYYMMDD.md`

Le JSON standardise:
- `date_heure`
- `source`
- `joueur`
- `type`
- `signature`
- `impact_stabilite`
- `cause_probable`
- `correlation`
- `preuve`

## Filtres prioritaires
- déconnexions:
  - `Player logout received`
  - `Disconnected from server`
  - `lost connection`
  - `Server closed`
- erreurs client:
  - `Failed to resolve uniform`
  - `[FANCYMENU] Failed to read`
  - `Received attachment change for unknown target`
  - `Received passengers for unknown entity`
- erreurs serveur:
  - `Can't keep up!`
  - `Stopping the server`
  - `Unable to close Phantom Array`
  - `Generation for section .* expired`
  - `WorldGen requiring .* outside the expected range`
  - `C2ME missing`

## Règle de tri
- `corrélé`:
  - même joueur
  - même seconde ou même fenêtre d'incident
  - signatures compatibles entre client et serveur
- `client-only`:
  - événement visible dans les logs client
  - aucune preuve serveur associée dans la même fenêtre
- `serveur-only`:
  - événement visible côté serveur
  - aucune preuve client disponible ou aucun symptôme client corrélé

## Interprétation minimale
- ne pas conclure à une instabilité serveur à partir d'un crash shader/UI client seul
- distinguer un `Server closed` propre d'un crash:
  - arrêt propre: `Stopping the server`, sauvegarde des mondes, redémarrage ensuite
  - crash: watchdog, stacktrace serveur bloquante, redémarrage sans séquence d'arrêt propre
- pour `Distant Horizons`:
  - vérifier le mode (`INTERNAL_SERVER`, `PRE_EXISTING_ONLY`)
  - noter les changements de mode lancés pendant qu'un joueur est connecté
  - considérer `Unable to close Phantom Array` + `Generation ... expired` comme un risque serveur actif, même sans déconnexion immédiate
