# Runbook: Crash au demarrage

## Collecte rapide
1) Etat du conteneur:
```bash
docker compose ps
```
2) Logs serveur:
```bash
docker compose logs --tail=500 cobblemon
```
3) Crash reports:
```bash
ls -la ./data/crash-reports 2>/dev/null || true
sed -n '1,200p' ./data/crash-reports/*.txt 2>/dev/null || true
```
4) Log applicatif principal:
```bash
sed -n '1,240p' ./data/logs/latest.log 2>/dev/null || true
```

## Causes probables
- Echec telechargement/modpack corrompu.
- Memoire insuffisante.
- Donnees partielles dans `./data` suite a un premier boot incomplet.

## Actions progressives (safe-first)
1) Verifier image et variables:
```bash
docker compose images
docker compose config | sed -n '/environment:/,/volumes:/p'
```
2) Refaire un demarrage propre sans toucher au monde:
```bash
docker compose down
rm -rf ./data/modrinth 2>/dev/null || true
docker compose up -d
```
3) Si besoin, augmenter `MEMORY` dans `.env`, puis redemarrer.
4) Si echec persistant: restaurer un backup (`runbooks/restore.md`).

## Escalade
- Conserver `latest.log` + crash report pour analyse.
