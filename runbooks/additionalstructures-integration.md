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

Si tu viens de modifier localement `datapacks/additionalstructures_1211/`, `datapacks/acm_pokemon_worldgen/`, un script `infra` associe ou ce runbook, synchronise le serveur avant toute commande Linux:

```powershell
./infra/deploy-server.ps1 -CreateRemoteBackup -VerifyService
```

Reference: `runbooks/server-sync.md`

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

## 2) Initialiser le nouveau monde ACM + AS (recommande)

```bash
./infra/openworld-village-init.sh --with-additionalstructures
```

Ce flux integre:
- creation du nouveau monde open world
- installation ACM (`acm_pokemon_worldgen`)
- installation AS (`additionalstructures_1211`)
- restarts forces pour appliquer les registries worldgen
- validation stricte ACM+AS avant pre-generation
- demarrage de Chunky seulement apres validation

## 3) Flux manuel (fallback / maintenance)

Utiliser ce flux seulement si tu ne passes pas par `openworld-village-init.sh --with-additionalstructures`:

```bash
./infra/install-pokemon-worldgen-datapack.sh --restart
./infra/install-additionalstructures-datapack.sh --new-world --allow-existing-world
./infra/validate-worldgen-datapacks.sh
```

Notes:
- `install-additionalstructures-datapack.sh` bloque par defaut si des regions overworld existent.
- `--allow-existing-world` est reserve a un bootstrap controle (ex: tout debut de vie du monde, avant exploration reelle).
- n'utilise pas ce flux pour retrofiter un monde en production deja explore.

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

1. si tu as utilise `openworld-village-init.sh --with-additionalstructures`, la pregen est deja demarree
2. suivre la progression Chunky et verifier logs/perf
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
