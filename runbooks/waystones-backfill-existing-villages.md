# Backfill Waystones dans les villages deja generes

Objectif: poser une `Waystone` dans les villages deja generes d'une map existante, sans reset du monde.

Script utilise:
- `./infra/waystones-backfill-villages.py`

Principe (v1):
- scan offline des villages via les structures dans les chunks (`.mca`)
- placement online via `./infra/mc.sh` (forceload + commande native `waystones place`)
- journal JSONL pour reprise (`--resume`)

Comportement de nommage (version actuelle):
- les waystones creees sont nommees automatiquement (`Village Plains 01`, `Village Savanna 02`, etc.)
- cela evite les waystones `<unnamed>` (inutilisables / mal enregistrees)

## Preconditions
- `Waystones` + `Balm` deja installes (serveur) et serveur demarre correctement
- sauvegarde recente possible
- fenetre de maintenance (ou periode tres calme)

## 1. Backup (obligatoire)
```bash
./infra/backup.sh
```

## 2. Dry-run / scan (liste des villages detectes)
```bash
python3 infra/waystones-backfill-villages.py \
  --scan-only \
  --out ./logs/waystones-backfill-plan.json
```

Verifier:
- `villages_selected` > 0
- les centres (`center`) paraissent plausibles

## 3. Batch pilote (recommande)
Commencer sur quelques villages pour valider le placement:

```bash
python3 infra/waystones-backfill-villages.py \
  --execute \
  --limit 3 \
  --journal ./logs/waystones-backfill.jsonl \
  --out ./logs/waystones-backfill-run1.json \
  --verbose
```

Puis verifier en jeu:
- une waystone a bien ete posee
- la position est acceptable dans le village

## 4. Batch complet (par tranches)
Executer par tranches et reprendre avec `--resume`:

```bash
python3 infra/waystones-backfill-villages.py \
  --execute \
  --limit 20 \
  --offset 0 \
  --resume \
  --journal ./logs/waystones-backfill.jsonl \
  --out ./logs/waystones-backfill-batch.json
```

Relancer ensuite avec la meme commande (ou autre `--limit`/`--offset`) tant que tous les villages ne sont pas traites.

## Options utiles
- `--min-distance-spawn <N>`: ignorer les villages trop proches du spawn (ex: si vous voulez poser a la main au spawn)
- `--force`: autorise le remplacement du bloc cible (le bloc au-dessus doit rester libre)
- `--search-radius-primary 8 --search-radius-fallback 16`: rayon de recherche local autour du centre estime du village
- `--place-block waystones:waystone`: override si l'id bloc change

## Journal / reprise
Journal par defaut:
- `./logs/waystones-backfill.jsonl`

Le script ecrit une ligne JSON par village traite:
- `placed`
- `placed_already`
- `skipped` (ex: `no_valid_spot`)
- `failed`

Avec `--resume`, les villages deja `placed`/`placed_already` sont ignores.

## Limitations (v1)
- Le scan detecte les villages via les structure starts, mais le point de pose est une approximation autour du centre du village.
- Pas de nommage/activation automatique de la waystone.
- Pas de retro-generation "native" dans les chunks; on fait un placement admin via commande.

## Rollback (si placement non satisfaisant)
Option rapide (si beaucoup de placements / doute):
1. `./infra/stop.sh`
2. `./infra/restore.sh backups/<backup>.tar.gz`
3. `./infra/start.sh`

Option manuelle (si peu de placements):
- retirer/casser les waystones posees en jeu (admin/creative)
