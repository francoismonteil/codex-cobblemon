# Village Pokecenter: Worldgen (Legacy)

> Ce runbook est legacy.
> Flux de reference en production: `runbooks/pokemon-worldgen.md` avec datapack unique `acm_pokemon_worldgen`.
> `./infra/install-pokemon-worldgen-datapack.sh` n'installe pas `acm_village_pokecenter`, uniquement `acm_pokemon_worldgen`.

Objectif:
- Documenter l'ancienne approche Pokecenter via datapack dedie (historique uniquement).

Limites / realite:
- Cela ne modifie que les **nouveaux villages** (nouveaux chunks).
- Selon la place disponible, le Pokecenter peut ne pas se poser partout.
- Avec l'approche "houses pool", il n'y a pas de garantie stricte "exactement 1 par village", mais on peut
  ajuster la frequence via le `weight` dans les pools.

## Contenu
- Datapack: `datapacks/acm_village_pokecenter/`
  - Template: `data/acm/structure/village/pokecenter.nbt`
  - Overrides vanilla pools:
    - `data/minecraft/worldgen/template_pool/village/*/houses.json`
    - `data/minecraft/worldgen/template_pool/village/*/zombie/houses.json`

Le template inclut un jigsaw `minecraft:building_entrance` pour etre compatible avec les routes de village.

## Installation (serveur)

Flux recommande (actuel):
1. Suivre `runbooks/pokemon-worldgen.md`.
2. Installer avec `./infra/install-pokemon-worldgen-datapack.sh` (ou `--restart`).

Legacy uniquement:
1. Copier dans le monde + reload:
   - `./infra/install-village-pokecenter-datapack.sh`
2. Redemarrer (recommande / souvent necessaire pour worldgen):
   - `./infra/safe-restart.sh`

## Verification
Dans le jeu (nouveaux chunks):
- Explorer et trouver un nouveau village.
- Le Pokecenter est une piece type "house" et peut apparaitre proche d'une route.
