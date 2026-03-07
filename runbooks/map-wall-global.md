# Mur de carte globale (en jeu, via cartes vanilla)

Objectif: afficher une vraie carte globale **dans le jeu** avec des `filled_map` en item frames (pas une carte web externe).

Ce flux reutilise les maps deja creees dans `./data/world/data/map_*.dat` et place automatiquement un mur.

## Prerequis
- Monde actif present dans `./data/world`.
- Serveur lance (`cobblemon`).
- Droits OP pour executer des commandes.
- Maps vanilla de la zone deja creees au niveau cible (recommande: `scale=4`).

## 1) Planifier la grille attendue
Par defaut, l'outil cible une zone carree `4000x4000` centree sur le spawn (typique open world actuel) avec des maps niveau 4.

```bash
python3 ./infra/map-wall-global.py
```

Sortie utile:
- taille de grille (ex: `2 x 2` pour 4000 blocs en scale 4),
- maps trouvees / manquantes,
- centres manquants a couvrir.

Option JSON:

```bash
python3 ./infra/map-wall-global.py --json-out ./logs/map-wall-plan.json
```

## 2) Creer les maps manquantes (si besoin)
Quand des centres sont manquants, teleporte-toi a chaque centre, cree/ouvre une map et monte-la au niveau voulu (cartography table), puis relance le plan.

Exemple de teleport:

```bash
./infra/mc.sh "tp <player> <center_x> 120 <center_z>"
```

Continue jusqu'a obtenir `missing: 0`.

## 3) Poser automatiquement le mur de cartes
Choisis l'ancre du coin haut-gauche du mur (`--wall-x --wall-y --wall-z`) et la direction de face (`--facing`).

Exemple:

```bash
python3 ./infra/map-wall-global.py \
  --apply \
  --wall-x 30 --wall-y 90 --wall-z 5 \
  --facing south
```

Ce que fait `--apply`:
- nettoie les item frames dans la zone cible,
- place un mur support (`minecraft:polished_andesite` par defaut),
- pose des item frames,
- injecte les `filled_map` par `map_id`.

## Options utiles
- `--diameter 6000` : adapter la taille cible.
- `--center-x ... --center-z ...` : changer le centre.
- `--x-min --x-max --z-min --z-max` : borne explicite (remplace center/diameter).
- `--scale 3` : autre niveau de map.
- `--frame-type item_frame` : cadre normal (sinon `glow_item_frame` par defaut).
- `--wall-block minecraft:stone_bricks` : bloc de fond.
- `--allow-missing` : autorise une pose partielle meme avec des tuiles manquantes.

## Notes operationnelles
- Le script **ne genere pas** de nouvelles maps automatiquement; il place celles deja presentes dans les `map_*.dat`.
- L'ordre d'affichage suit la grille X/Z attendue de la zone cible.
- Si des maps sont trouvees avec un centre voisin mais pas exact, elles peuvent etre utilisees en mode `nearest` (visible dans le plan).
