# Runbook: Lag / TPS

## Signaux
- Warnings `Can't keep up!` dans les logs.
- Freezes joueurs ou chunks lents a charger.
- CPU eleve ou memoire proche de la limite du conteneur.

## Collecte
```bash
docker compose logs --tail=300 cobblemon
docker stats --no-stream
sed -n '1,240p' ./data/logs/latest.log 2>/dev/null || true
```

## Actions progressives (sans changer de modpack)
1) Verifier la memoire effective:
```bash
grep '^MEMORY=' .env
docker inspect cobblemon --format '{{range .Config.Env}}{{println .}}{{end}}' | grep '^MEMORY='
```
2) Ajuster distances si besoin (`data/server.properties`):
- `view-distance` entre `6` et `8`
- `simulation-distance` entre `5` et `7`
3) Limiter les pics:
- Eviter pregen/changements massifs en pleine session.
- Redemarrer hors heures de jeu (deja automatise a 05:00).
4) Si saturation persistante:
- Monter `MEMORY` par paliers de `256M` max, puis mesurer 24h.

## Criteres OK
- Pas de warnings `Can't keep up!` repetes.
- Server ressenti fluide pour 4 joueurs.

## Criteres KO
- Lag regulier malgre ajustements.
- Utilisation memoire conteneur > 95% frequente.
