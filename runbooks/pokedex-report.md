# Runbook: Rapport Pokedex serveur

## Objectif

Generer un rapport detaille du Pokedex serveur Cobblemon:
- liste exhaustive `seen` / `caught` / `encountered_only` par joueur
- union des especes deja vues/capturees sur le serveur
- comparaison avec le roster complet expose par `data/showdown/data/pokedex.js`
- mise en relation avec le temps de jeu lu depuis `data/world/stats/*.json`

Le flux est entierement local au serveur et ne depend pas d'une API externe.

## Entree

Le script lit:
- `./data/usercache.json`
- `./data/world/pokedex/<uuid>.nbt`
- `./data/world/stats/<uuid>.json`
- `./data/showdown/data/pokedex.js`

## Commande de base

Depuis le repo sur le serveur Linux:

```bash
python3 ./infra/pokedex-report.py
```

Sortie par defaut:

```text
./audit/pokedex-comparison-YYYYMMDD.md
```

## Variantes utiles

Ecrire dans un fichier specifique:

```bash
python3 ./infra/pokedex-report.py --output ./audit/pokedex-comparison-custom.md
```

Afficher aussi le rapport dans le terminal:

```bash
python3 ./infra/pokedex-report.py --stdout
```

Publier directement sur Discord via le webhook configure dans `.env`:

```bash
set -a; source ./.env; set +a
python3 ./infra/pokedex-report.py --discord
```

Publier sur un webhook explicite:

```bash
python3 ./infra/pokedex-report.py \
  --discord \
  --discord-webhook-url "https://discord.com/api/webhooks/..."
```

Personnaliser le message d'accompagnement:

```bash
python3 ./infra/pokedex-report.py \
  --discord \
  --discord-message "Rapport detaille Pokedex serveur au 2026-03-01 en piece jointe."
```

## Notes d'interpretation

- `seen` signifie qu'une espece est marquee `ENCOUNTERED` ou `CAUGHT` dans le Pokedex serveur.
- `caught` signifie qu'une espece est marquee `CAUGHT`.
- `encountered_only` signifie qu'elle a ete vue mais pas encore capturee.
- `couverture du monde vu` = part du catalogue deja vu sur ce serveur que couvre le joueur.
- `couverture du roster complet` = part du roster implemente dans la stack actuelle.

## Limites

- Le roster complet est derive de `data/showdown/data/pokedex.js`.
- Le script compte les especes de base, pas chaque forme alternative comme une espece distincte.
- Si un joueur n'a pas de fichier Pokedex ou stats, le script echouera tant que la donnee manque.
