# acm_windmills

Datapack worldgen + placement manuel pour `acm:windmill`.

Important:
- `data/acm/structure/windmill.nbt` doit etre (re)genere depuis le schematic local (gitignore) via:
  - `./infra/build-windmill-structure.sh`
  - Le script cree aussi un alias `acm:windmill_template` pour les placements manuels via `/place template`.
  - Par defaut, le builder supprime le "terrain pad" (terre/sable/gravier) du schematic pour mieux se fondre dans l'environnement.

Suppression "one-liner" en jeu:
- Effacer un windmill colle via template:
  - `execute positioned <x> <y> <z> run function acm:windmill/clear`
  - `<x> <y> <z>` = l'origine utilisee pour `place template acm:windmill_template <x> <y> <z>`
