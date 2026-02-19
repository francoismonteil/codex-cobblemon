# Pokemon Worldgen Progress

Updated: 2026-02-19

## Goal
- Build 3 Pokemart variants per village biome.

## Biome Status
- plains: 3/3 done
  - pokemart_plains_small
  - pokemart_plains_medium
  - pokemart_plains_large
  - integrated in village generation (`houses` normal + zombie)
- desert: 3/3 done
  - pokemart_desert_small
  - pokemart_desert_medium
  - pokemart_desert_large
  - integrated in village generation (`houses` normal + zombie)
- savanna: 2/3 in progress
  - pokemart_savanna_medium
  - pokemart_savanna_large
  - missing: pokemart_savanna_small
  - generation integration pending until small is created
- snowy: 0/3
- taiga: 0/3

## Next Step
1. Create `pokemart_savanna_small`.
2. Inject savanna small/medium/large in `village/savanna/houses` (normal + zombie) with weights 1/1/2.
