# Windmill: Worldgen + Placement Manuel (Plan)

Objectif:
- Avoir un windmill qui apparait *proceduralement* dans le monde (worldgen datapack).
- Garder en plus une option de placement manuel (scripts infra) pour en ajouter apres coup.
- Densite cible: **max 1 windmill par zone ~640x640 blocs**.

Contexte repo:
- Serveur: Minecraft 1.21.1 (Fabric)
- Schematic source: `downloads/Windmill - (mcbuild_org).schematic` (MCEdit/WorldEdit "Alpha")
- Converter existant (command stream): `infra/schematic-mcedit-to-commands.py`
- Paste via console: `infra/spawn-schematic-mcedit.sh`

## 1) Convertir le `.schematic` en template structure `.nbt`

But:
- Convertir le format "Alpha schematic" en **structure template** moderne utilisable par:
  - `place template <template>`
  - `place structure <structure>` (via worldgen)

Travail a faire:
1. Creer un script: `infra/schematic-mcedit-to-structure-nbt.py`
2. Reutiliser:
   - Parsing NBT (present dans `infra/schematic-mcedit-to-commands.py`)
   - Mapping bloc legacy -> bloc moderne (fonction `map_block`)
3. Normalisation recommandee:
   - Appliquer `WEOffsetX/Y/Z` du schematic.
   - Recaler pour que le min (x,y,z) devienne (0,0,0).
4. Ecrire un fichier NBT "structure template" (palette + blocks) pour 1.21.1.
5. Sortie attendue:
   - `datapacks/acm_windmills/data/acm/structure/windmill.nbt`
   - Note: dossier **`structure/`** (pas `structures/`).

Notes:
- Le windmill (mcbuild_org) est generalement simple (peu/pas de block entities). Si des block entities existent
  (coffres, panneaux, etc.), il faudra aussi porter leur NBT dans le template.

## 2) Creer le datapack worldgen `acm_windmills`

Arborescence cible:
1. `datapacks/acm_windmills/pack.mcmeta`
2. `datapacks/acm_windmills/data/acm/structure/windmill.nbt` (etape 1)
3. `datapacks/acm_windmills/data/acm/worldgen/template_pool/windmill/start.json`
4. `datapacks/acm_windmills/data/acm/worldgen/structure/windmill.json`
5. `datapacks/acm_windmills/data/acm/worldgen/structure_set/windmills.json`
6. `datapacks/acm_windmills/data/acm/tags/worldgen/biome/has_windmill.json`

### 2.1 pack.mcmeta
- Minecraft 1.21.1 => `pack_format: 48`

### 2.2 Biomes (plaines)
- `.../tags/worldgen/biome/has_windmill.json`
  - inclure au minimum `minecraft:plains`
  - optionnel: `minecraft:sunflower_plains`

### 2.3 Template pool
- `.../worldgen/template_pool/windmill/start.json`
- Un seul element de type `single_pool_element` pointant vers `acm:windmill`
- Projection: `rigid`
- Processors: `minecraft:empty`

### 2.4 Structure (jigsaw minimal)
- `.../worldgen/structure/windmill.json`
- Type: `minecraft:jigsaw`
- `start_pool`: `acm:windmill/start`
- `size`: 1
- Important: ne pas exiger un jigsaw block dans le template (donc ne pas forcer `start_jigsaw_name`).
- Pose au sol:
  - `project_start_to_heightmap`: `WORLD_SURFACE_WG` (ou `WORLD_SURFACE` selon comportement desire)
  - Definir `start_height` de maniere standard (selon schema 1.21)
- Limiter aux biomes:
  - `biomes`: `#acm:has_windmill`

### 2.5 Structure set (densite: ~1 / 640x640)
- 640 blocs = 40 chunks (40*16)
- `.../worldgen/structure_set/windmills.json`
  - `placement.type`: `minecraft:random_spread`
  - `spacing`: **40**
  - `separation`: **20** (valeur typique < spacing)
  - `salt`: un int stable (ex: 123456789)

Interpretation:
- `spacing=40` limite le *maximum theorique* a environ 1 structure par cellule 40x40 chunks (~640x640 blocs).
- La rarete finale depend aussi de la validite du biome, de la generation des chunks, etc.

## 3) Installer le datapack dans le monde

Sur le serveur (monde courant):
1. Copier le dossier:
   - vers `data/world/datapacks/acm_windmills/`
2. Recharger:
   - commande console: `reload`
   - IMPORTANT: les registres worldgen (structures, structure_set, etc.) ne sont pas toujours rechargeables via `reload`.
     Si `place structure acm:windmill ...` dit "There is no structure with type", faire un **restart serveur**.
3. Verifier:
   - `datapack list enabled` doit inclure `file/acm_windmills`

## 4) Validation (tests rapides)

Commandes utiles en console:
1. Placement worldgen "manuel":
   - `place structure acm:windmill <x> <y> <z>`
2. Placement template:
   - `place template acm:windmill_template <x> <y> <z>`
3. Suppression (one-liner, si place template):
   - `execute positioned <x> <y> <z> run function acm:windmill/clear`

## 5) Placement manuel via script infra (apres coup)

But:
- Placer un windmill a un endroit precis, au sol, sans WorldEdit.

Option A (recommandee une fois le datapack en place):
1. Ajouter `infra/spawn-windmill-template.sh`:
   - calcule un `y` "sol" (via `infra/world-height-at.py`)
   - fait `forceload add`
   - execute `place template acm:windmill x y z`
   - fait `forceload remove`

Option B (deja existante, independante du datapack):
- Continuer a utiliser:
  - `infra/spawn-schematic-mcedit.sh` (colle le `.schematic` via setblock/fill)

## 6) Integration a la creation d'une map

But:
- Installer le datapack avant la generation initiale pour que les structures apparaissent naturellement.

Approche:
1. Modifier `infra/new-world-and-spawn.sh`:
   - copier `datapacks/acm_windmills` dans `data/world/datapacks/` *avant* le premier demarrage du serveur
2. Demarrer le serveur, generer des chunks normalement:
   - les windmills apparaitront lors de la generation de nouvelles zones (plaines).

## Notes / Garde-fous

- La conversion `.schematic -> .nbt` doit produire un template correct pour 1.21.1:
  - palette stable
  - blocks avec positions
  - (optionnel) block entities
- Si le windmill doit etre "propre" sur terrain:
  - prevoir une "foundation" ou un petit terraform (processors) si necessaire
  - sinon, il suivra le relief (ou se plantera) selon le heightmap/placement.
