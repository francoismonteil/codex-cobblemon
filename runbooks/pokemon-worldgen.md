# Pokemon Worldgen (datapack unique)

Objectif:
- utiliser un seul datapack: `datapacks/acm_pokemon_worldgen`
- generer automatiquement Pokecenters + Pokemarts dans les villages vanilla
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
   - Pokecenter present dans `town_centers`
   - Pokemart present dans `houses`
4. Verifier les logs serveur (pas d'erreur datapack/worldgen).

## Notes

- Les anciens packs (`acm_village_pokecenter`, `acm_windmills`) restent dans le repo pour historique.
- Le flux recommande en production est maintenant `acm_pokemon_worldgen`.
