# Client Pack Academy V2

Objectif: definir le futur pack client obligatoire pour l'ouverture Academy sur la base
Cobblemon 1.7.3 actuelle.

## Regle de support

- Nouveau profil obligatoire
- Auto-update desactive
- L'ancien profil n'est plus considere supporte sur l'ouverture Academy

## Base

- Minecraft: `1.21.1`
- Loader: `Fabric`
- Base modpack: `Cobblemon Official Modpack [Fabric] 1.7.3`

## Ajouts Academy V2 supportes maintenant

### Quetes / equipes / utilitaires FTB
- `FTB Library` -> `2101.1.31`
- `FTB Teams` -> `2101.1.9`
- `FTB Essentials` -> `2101.1.9`
- `FTB Quests` -> `2101.1.23`
- `ExtraQuests` -> `1.6.2`

### Economie / progression
- `Numismatic Overhaul` -> `0.3.5+1.21`

### Gym path (apres validation staging)
- `RCT API` -> `0.15.0-beta`
- `Admiral` -> `0.4.10+1.21.1`
- `RAD Gyms` -> `0.4.4`

### Dimension Academy (apres pregen + staging)
- `Eternal Starlight` -> `0.7.0-hotfix+1.21.1+fabric`

## Bloque a ce jour

- `StarAcademyMod / Academy Integration`
- `Academy Safari`
- `Academy Houses`
- `Acceptance letters`
- `House Pokedex`

Raison:

- le repo upstream Academy compile encore contre `Cobblemon 1.6.1+1.21.1`
- la base actuelle du serveur est `Cobblemon 1.7.3+1.21.1`
- le depot ne doit pas prendre un fork durable juste pour franchir cet ecart

## Source de verite

- lock machine-readable: `modpack/academy-v2/stack.lock.json`
- audit operateur: `./infra/academy-compat-audit.py`
