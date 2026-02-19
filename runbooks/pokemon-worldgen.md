# Pokemon Worldgen (datapack unique)

Objectif:
- utiliser un seul datapack: `datapacks/acm_pokemon_worldgen`
- generer automatiquement des Pokemarts dans les villages vanilla (biomes en cours)
- reconstruire tous les `.nbt` depuis des plans versionnes

## Source des structures

- Plans: `tools/structgen/plans/**`
- Templates NBT: `tools/structgen/templates/**`
- Compileur: `tools/structgen/compile.py`

## Regeneration

Windows:

```powershell
./tools/structgen/regen.ps1
```

Linux:

```bash
./tools/structgen/regen.sh
```

## Installation sur serveur

```bash
./infra/install-pokemon-worldgen-datapack.sh
```

Option avec restart direct:

```bash
./infra/install-pokemon-worldgen-datapack.sh --restart
```

## Verification

1. `reload` puis restart serveur (recommande pour worldgen registries).
2. Explorer des nouveaux chunks.
3. Verifier dans les villages:
   - Pokemart present dans `houses`
4. Verifier les logs serveur (pas d'erreur datapack/worldgen).

## Notes

- Le Pokecenter est gere nativement par Cobblemon (pas par ce datapack).
- Les anciens packs (`acm_village_pokecenter`, `acm_windmills`) restent dans le repo pour historique.
- Le flux recommande en production est maintenant `acm_pokemon_worldgen`.
