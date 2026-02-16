# structgen

Pipeline reproductible pour générer des structures `.nbt` (format Structure Block) depuis des plans JSON versionnés.

## Entrées

- Plans:
  - `tools/structgen/plans/pokecenter/*.json`
  - `tools/structgen/plans/pokemart/*.json`
- Templates NBT:
  - `tools/structgen/templates/block_entities/*.nbt`
  - `tools/structgen/templates/entities/*.nbt`
- Règles bloc/state:
  - `tools/structgen/allowlist_blocks.json`

## Sortie

- `datapacks/acm_pokemon_worldgen/data/acm/structure/village/*.nbt`

## Commandes

Windows:

```powershell
./tools/structgen/regen.ps1
```

Linux/macOS:

```bash
./tools/structgen/regen.sh
```

CLI directe:

```bash
py -3 tools/structgen/compile.py --out datapacks/acm_pokemon_worldgen/data/acm/structure --include-entities
```

Options utiles:

- `--rotate 0|90|180|270`
- `--mirror none|left_right|front_back`
- `--include-entities`
- `--biome plains --biome desert ...`

## Workflow

1. Modifier un plan JSON (`tools/structgen/plans/...`).
2. Régénérer les structures (`regen.ps1` ou `regen.sh`).
3. Installer/mette à jour le datapack sur le serveur.
4. `reload` puis redémarrage serveur (recommandé pour worldgen registries).
5. Tester dans de nouveaux chunks.

## Validation

Le compilateur rejette:

- blocs hors allowlist
- propriétés/valeurs de state non allowlistées
- positions hors bornes de `size`
- jigsaw incomplets/invalides
- templates `.nbt` manquants
