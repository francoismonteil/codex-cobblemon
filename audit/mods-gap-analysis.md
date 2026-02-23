# Audit d'ecart - Mods Cobblemon (style PokéRayou generique)

Date d'audit: 2026-02-22 (UTC, voir `audit/mods-current-inventory.json`)

## Perimetre
- Base analysee: `Cobblemon Official Modpack [Fabric] 1.7.3` (`MC 1.21.1`, `Fabric`)
- Sources:
  - `manifest.Lydu1ZNo.json` (modpack pinne)
  - scripts `infra/mods-install-*.sh` (extras prevus)
  - `audit/mods-current-inventory.{csv,json}` (genere par `tools/mod_audit.py`)
- Limitation majeure:
  - `./data/mods` absent localement, donc **pas de verification runtime** des jars reellement charges sur le serveur.

## Resultat de l'inventaire (etat actuel observable)
- `76` mods detectes dans le modpack officiel (source `modpack_manifest`)
- `4` mods extras prevus par scripts repo (source `repo_script`) :
  - `Chunky`
  - `Flan`
  - `Waystones`
  - `Balm` (dependance de Waystones)
- `0` mod observe depuis `data/mods` (dossier absent)

### Repartition side (modpack officiel)
- `48` `client_required`
- `25` `both`
- `3` `server_only`

### Constats clefs (mods deja couverts par le modpack)
- UI/navigation deja riche:
  - `Xaero's Minimap`
  - `Xaero's World Map`
  - `EMI` (+ addons)
  - `JEI`
- Perf deja correcte cote pack:
  - `Lithium`
  - `FerriteCore`
  - `Krypton`
  - plusieurs optimisations client (`Sodium`, etc.)
- Quelques utilitaires serveur deja presents:
  - `Let Me Despawn`
  - `NetherPortalFix`
  - `Almanac`

## Overlaps / doublons detectes (repo vs modpack)
- `Balm` apparait deja dans le modpack officiel **et** dans `infra/mods-install-waystones.sh`
  - Ce n'est pas forcement un probleme: le script pinne explicitement la dependance de `Waystones`.
  - Risque operationnel faible si la version et le fichier restent identiques.

## Gaps par besoin (style "aventure Cobblemon" / PokéRayou generique)

| Besoin | Couvert par mod actuel ? | Couvert par datapack/script ? | Candidat(s) | Risque | Recommandation |
| --- | --- | --- | --- | --- | --- |
| Regroupement / transport rapide | Partiel (minimap/world map seulement) | Partiel (`spawn` outillage possible, mais pas de fast travel gameplay) | `Waystones` | Moyen (client requis, impact progression) | **Ajouter en phase 3** si vous voulez accelerer les trajets |
| Protection spawn / village | Non (dans le modpack) | Oui (scripts repo prevus) | `Flan` | Faible a moyen (config claims) | **Ajouter en phase 2** pour securiser le spawn |
| Exploration sans lag (generation) | Partiel (optimisations runtime) | Oui (pipeline pregen present) | `Chunky` | Faible | **Ajouter en phase 1/2** avant gros open-world |
| Supervision perf / diagnostic | Non (profiling detaille absent) | Monitoring infra present, mais pas profiler Minecraft | `spark` | Faible | **Ajouter en phase 1** |
| Immersion coop | Oui (chat + Discord vocal externe retenu) | Non | Option mod non retenue: `Simple Voice Chat` | Moyen (client requis + reseau/port) | **Rester sur Discord externe** (decision actuelle) |
| Reperage / navigation | Oui (`Xaero's Minimap` + `Xaero's World Map`) | Oui (runbooks + spawn village) | Aucun ajout prioritaire | Faible | **Ne pas ajouter** de seconde minimap |
| QoL inventaire / recettes | Oui (`JEI` + `EMI`) | n/a | Aucun ajout prioritaire | Faible | **Ne pas empiler** d'autres mods UI recette |
| Worldgen "identite Pokemon" | Partiel (Cobblemon + monde vanilla) | Oui (`acm_pokemon_worldgen`, `additionalstructures_1211`) | Datapacks existants | Eleve sur monde existant | Garder la voie datapack; reserver changements worldgen a un nouveau monde |

## Risques principaux a surveiller
- **Fausse certitude sur le serveur reel**: sans `data/mods` ni `latest.log`, on ne sait pas quels extras sont deja installes.
- **Doublons fonctionnels UI**: le modpack couvre deja minimap, world map, recipe UI; ajouter d'autres mods du meme type complique le client sans gain clair.
- **Worldgen en cours de vie du monde**: ajouter des mods/datapacks de structures apres generation cree des incoherences spatiales et des attentes joueurs incoherentes.
- **Client requis**: `Waystones` (et les mods QoL choisis comme backpack/YIGD) exigent une discipline de version cote joueurs.

## Action de validation manquante (pour passer de "theorique" a "verite terrain")
Quand `./data` est disponible localement (ou sur le serveur), lancer:

```powershell
py -3 tools/mod_audit.py --write --mods-dir .\data\mods
```

Puis completer avec un controle logs:
- `./data/logs/latest.log` (mods charges, erreurs de compat)
- `docker logs cobblemon --tail 300` (si conteneur local)

## Conclusion
Le modpack officiel couvre deja fortement la QoL et l'UI. Les vrais trous pour une aventure Cobblemon "PokéRayou-style" sont surtout:
1. `profiling/perf diagnostic` (`spark`)
2. `protection/claims` (`Flan`)
3. `mobilite de groupe` (`Waystones`)
4. `social voix` (couvert par Discord externe; pas de mod voix integre retenu)
