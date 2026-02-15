# Runbook: Spawn Ville Pokemon (Moderne)

Last updated: 2026-02-12

## Objectif
Un spawn "ville Pokemon" moderne et utile, sans ajouter de mods (via commandes vanilla + blocs Cobblemon).

## Decisions (verrouillees)
- Monnaie du shop: `emeralds`
- Gym: `decor + arene` (RP d'abord)

## Contraintes
- Pas de mod de structures/ville ni WorldEdit: tout doit etre fait via scripts (`/fill`, `/setblock`, `/summon`).
- Idempotent: on doit pouvoir relancer les scripts sans casser.
- Source de verite: scripts `infra/` (pas de "fait a la main non documente").

## Layout (zones)
- Centre: place + spawnpoint + signaletique
- Ouest: Pokecenter (heal + PC + services)
- Est: Pokemart (shop emeralds)
- Nord: Gym/Arene (decor + zone combat)
- Sud: Portails (nether frame + points pratiques)

## Phases

### Phase 1: Inventaire des utilites disponibles
- Lister les IDs items/blocs Cobblemon valides sur ce modpack.
- Output: liste "OK a utiliser" + "absent".

### Phase 2: Spawn core (place + batiments)
- Script unique de build spawn (sky plaza) a coordonnees fixes.
- Fixer `setworldspawn` + `gamerule spawnRadius 0`.

### Phase 3: Pokecenter utile
- `cobblemon:healing_machine`
- `cobblemon:pc`
- Zone craft/enchant + ender chest (pas de coffres publics par defaut)
- Signalisation simple

### Phase 4: Pokemart utile (shop emeralds)
- 2 a 3 PNJ vendeurs:
  - "Balls"
  - "Heals"
  - "Basics" (torches, nourriture, lit, etc.)
- PNJ hardenes (NoAI, Invulnerable, PersistenceRequired) + kiosks
 - Script: `infra/spawn-shop.sh`

### Phase 5: Gym/Arene (decor + zone)
- Construction deco + arene fermable (portes/grilles)
- Pas d'automatisation de combats (sans mod/plugin)
 - Script: `infra/spawn-gym.sh`

### Phase 6: Onboarding
- `infra/onboard.sh <Pseudo> [--op]` (deja present)
- `infra/starter.sh <Pseudo>` (kit de depart) et appel automatique depuis `onboard.sh` (best-effort)

### Phase 7: Securite/rollback
- Avant chaque phase "build": `infra/backup.sh` + copie secondaire (deja en place)
- Scripts separables:
  - `infra/build-modern-spawn.sh` (core)
  - `infra/spawn-shop.sh` (pokemart)
  - `infra/spawn-gym.sh` (gym)
  - `infra/starter.sh` (kit)
  - `infra/spawn-city.sh` (orchestrateur complet)

### Phase 8: Validation
- Logs: aucune erreur "Unknown block/item/entity"
- Gameplay:
  - arrive au spawn
  - heal + PC OK
  - achats OK
  - gym visitable
