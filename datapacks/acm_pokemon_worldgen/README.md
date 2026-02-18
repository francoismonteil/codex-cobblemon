# acm_pokemon_worldgen

Datapack worldgen Cobblemon (Minecraft 1.21.1):

- ajoute des Pokémarts dans les `houses` villages
- supporte `plains`, `desert`, `savanna`, `snowy`, `taiga` + variantes

Note:
- Les Pokécenters ne sont plus injectés par ce datapack (gérés nativement par Cobblemon).

## Source of truth

Les bâtiments ne sont pas construits à la main.
Les `.nbt` sont générés depuis les plans versionnés:

- `tools/structgen/plans/**`
- `tools/structgen/templates/**`

## Regénération

```powershell
./tools/structgen/regen.ps1
```

ou

```bash
./tools/structgen/regen.sh
```

## Installation serveur

```bash
./infra/install-pokemon-worldgen-datapack.sh
```

Option:

```bash
./infra/install-pokemon-worldgen-datapack.sh --restart
```

## Test en jeu

1. Générer/explorer de nouveaux chunks.
2. Trouver un village `plains` puis autres biomes.
3. Vérifier apparition (ou placement de test) du Pokémart.
4. Vérifier absence d'erreurs datapack/worldgen dans les logs serveur.
