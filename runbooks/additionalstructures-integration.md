# Additional Structures + ACM (Compat 1.21.1)

Objectif:
- ajouter un maximum de structures via datapack en gardant l'existant ACM
- imposer une compatibilite stricte Minecraft 1.21.1 avant installation
- deploiement sur **nouveau monde** uniquement

## Portee
- On **n'edite pas** `datapacks/acm_pokemon_worldgen`.
- AS est installe comme pack separe: `additionalstructures_1211`.
- Le gate compatibilite est bloquant: pas de deploiement si checks KO.

## Prerequis
- Source brute AS deposee dans `downloads/additionalstructures_1211/`.
- Jar de reference 1.21.1 present:
  - `downloads/AdditionalStructures-1.21.x-(v.5.1.0-fabric).jar`
- Monde cible neuf (nouvelle generation).

## 1) Normaliser et verifier AS (obligatoire)

```bash
./infra/prepare-additionalstructures-1211.sh
```

Effets:
- compare `downloads/additionalstructures_1211` a la reference v5.1.0 1.21.1
- genere les rapports:
  - `reports/additionalstructures_1211/<timestamp>/extra.txt`
  - `reports/additionalstructures_1211/<timestamp>/missing.txt`
  - `reports/additionalstructures_1211/<timestamp>/changed.txt`
- applique la politique par defaut:
  - `extra`: exclus
  - `missing`: bloquant
  - `changed`: bloquant (revue manuelle)
- produit le pack normalise:
  - `datapacks/additionalstructures_1211/`

## 2) Installer ACM + AS dans le nouveau monde

```bash
./infra/install-pokemon-worldgen-datapack.sh --restart
./infra/install-additionalstructures-datapack.sh --new-world
```

Notes:
- restart obligatoire pour les registries worldgen.
- n'utilise pas ce flux pour retrofiter un monde en production deja explore.

## 3) Validation stricte pre-prod

```bash
./infra/validate-worldgen-datapacks.sh
```

Ce script:
- valide statiquement AS (`pack_format`, JSON, refs worldgen)
- redemarre (sauf `--skip-restart`)
- scanne les logs recents pour erreurs datapack/worldgen
- stocke un snapshot logs:
  - `logs/validate-worldgen-datapacks.last.log`

## 4) Verification fonctionnelle in-game (nouveaux chunks)

Executer:

```mcfunction
/locate structure additionalstructures:well_1
/locate structure additionalstructures:maya_temple
/locate structure additionalstructures:tower_1
/locate structure minecraft:village_plains
```

Puis verifier:
- apparition reelle des structures AS
- presence des Pokemarts ACM dans de nouveaux villages

## 5) Pregen + go-live

1. lancer la pregen avec votre flux openworld (`Chunky`)
2. verifier logs/perf pendant la pregen
3. ouvrir le serveur joueurs seulement apres checklist verte

## Rollback

1. backup avant installation (`./infra/backup.sh`)
2. en echec:
   - restaurer backup monde + datapacks
   - restart (`./infra/safe-restart.sh`)
   - revalider baseline

## Commandes utiles
- `./infra/mc.sh "datapack list enabled"`
- `docker logs cobblemon --tail 400`
- `./infra/datapacks-prune-prev.sh`

