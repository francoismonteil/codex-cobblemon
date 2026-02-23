# Recommandations Mods - Aventure Cobblemon (inspiration PokéRayou)

## Contexte / hypotheses
- Base: `Cobblemon Official Modpack [Fabric] 1.7.3` (`MC 1.21.1`, `Fabric`)
- Style cible: "PokéRayou generique" = aventure fluide, exploration, progression Pokemon, confort de groupe, faible friction
- Serveur cible: petit groupe prive (~4 joueurs)
- Priorite: stabilite et simplicite operationnelle > volume de contenu
- Limitation de cet audit: `./data/mods` absent localement, donc la shortlist s'appuie sur:
  - le modpack officiel pinne
  - les scripts `infra/mods-install-*.sh`
  - les runbooks open-world (`Flan`, `Chunky`, datapacks worldgen)

## Mods deja presents (resume)
### Deja bien couverts (pas besoin d'ajouter)
- Navigation/UI:
  - `Xaero's Minimap`
  - `Xaero's World Map`
  - `JEI`
  - `EMI` + addons
- Perf de base:
  - `Lithium`, `FerriteCore`, `Krypton`
  - stack client `Sodium` (+ extras)
- QoL generale:
  - nombreuses ameliorations deja presentes (tooltips, animations, adv, etc.)

### Extras deja prepares dans le repo (non confirmes installes runtime)
- `Chunky` (via `infra/mods-install-openworld.sh`)
- `Flan` (via `infra/mods-install-openworld.sh`)
- `Waystones` + `Balm` (via `infra/mods-install-waystones.sh`)

## Ecarts / overlaps / risques
### Gaps fonctionnels reels
- `Profiling / diagnostic serveur` detaille: **manquant** (`spark` recommande)
- `Protection spawn/claims`: **manquant dans le modpack**, mais outillage repo deja prevu (`Flan`)
- `Fast travel gameplay`: **manquant** (`Waystones`)
- `Voix proximite / immersion groupe`: non retenu pour l'instant (choix: vocal externe type Discord)

### Overlaps detectes
- `Balm` est deja dans le modpack et aussi pinne dans le script `Waystones`
  - OK si meme version/fichier (cas actuel detecte dans l'audit repo)

### Risques structurants
- Ajouter des mods worldgen/structures sur un monde existant => risque de generation incoherente
- Ajouter des mods UI redondants => friction client inutile
- Ajouter trop de mods "confort" => casse le rythme progression/exploration si l'aventure devient trop triviale

## Grille de scoring (style PokéRayou generique)
Pondérations:
- Exploration & decouverte: `25%`
- Progression Pokemon / aventure: `20%`
- Confort de groupe / mobilite: `20%`
- Immersion & ambiance: `10%`
- Lisibilite / QoL: `10%`
- Stabilite serveur: `15%`

Regles de malus:
- Gros malus si `worldgen_risk` eleve sur monde deja existant
- Malus moyen si `client_friction` eleve (mod client requis pour tout le groupe)

## Evaluation des candidats (par bucket)

### Travel / mobilite
- **Waystones** (repo deja prepare) -> excellent confort de groupe, faible complexite de setup
- Alternative a evaluer: `homes/teleports` via scripts/commandes serveur (hors mod) -> plus simple mais moins "gameplay"

### Exploration / structures legeres
- **Datapack `additionalstructures_1211`** (repo deja outille) -> bonne ambiance, mais **nouveau monde recommande**
- Alternative a evaluer: autre datapack structures legeres -> meme contrainte worldgen

### QoL aventure
- Etat actuel du pack: deja riche (`JEI`, `EMI`, minimap/worldmap, tooltips)
- Options a evaluer seulement si douleur utilisateur reelle:
  - `Mouse Tweaks` (si absent)
  - `Inventory Profiles Next` (si absent)
- Decision par defaut: **pas d'ajout** dans ce bucket

### Social / groupe
- Option mod non retenue: **Simple Voice Chat** (forte immersion, mais plus de friction reseau/client)
- Choix retenu: Discord vocal externe -> zero friction technique cote serveur

### Admin / anti-grief / claims
- **Flan** (repo deja prepare) -> bon fit pour protection spawn/village
- Option complementaire (si serveur plus public): mod d'audit/rollback type `Ledger` (a valider selon vos besoins)

### Perf / diagnostic
- **Chunky** -> pre-generation (reduction du lag d'exploration)
- **spark** -> profiler pour diagnostiquer TPS/CPU/ticks lents

### Ambiance Pokémon
- Le pack a deja une bonne base ambiance/cosmetique cote client
- Le repo fournit deja un meilleur levier "identite Pokemon" via scripts/datapacks/spawn (`healer`, `PC`, prefab, village spawn)
- Decision par defaut: **privilegier l'habillage spawn + points d'interet** plutot qu'ajouter de nouveaux mods cosmetiques

## Shortlist priorisee

### Must (ajouter maintenant)
- `spark` (server-only, diagnostic)
  - Pourquoi: manque le plus important pour exploiter un serveur durable sans debug a l'aveugle
  - Risque: faible
- `Flan` (claims/protection spawn)
  - Pourquoi: aligne avec le runbook open-world et protege le spawn/village
  - Risque: faible a moyen (regles de claims a expliquer)
- `Chunky` (pre-generation)
  - Pourquoi: cle pour exploration fluide sur Cobblemon open-world
  - Risque: faible si utilise pendant maintenance

### Should (ajouter apres test)
- `Waystones` (avec `Balm`, deja dans le modpack)
  - Pourquoi: reduit les temps morts, tres fort pour sessions groupe
  - Risque: moyen (impact progression + client requis)
  - Note: `Balm` est deja present dans le modpack officiel, verifier seulement la coherence des versions

### Maybe (a prototyper)
- `Ledger` (ou equivalent audit/rollback Fabric)
  - Pourquoi: utile si vous ouvrez le serveur a plus de joueurs / anti-grief post-mortem
  - Risque: faible a moyen, utilite faible sur groupe prive tres restreint
- `Additional Structures` (via datapack deja outille dans le repo)
  - Pourquoi: exploration plus vivante
  - Risque: eleve sur monde existant; a reserver a un **nouveau monde** ou a une regen planifiee
- QoL supplements (`Mouse Tweaks`, `Inventory Profiles Next`) **seulement si besoin explicite des joueurs**

### Avoid (a eviter, avec raison)
- Ajouter une autre minimap / world map (`JourneyMap`, etc.)
  - Raison: doublon avec `Xaero's Minimap` + `Xaero's World Map`
- Ajouter un autre gros mod de recipe UI/lookup
  - Raison: `JEI` + `EMI` sont deja presents
- Ajouter des mods worldgen lourds en plein milieu de vie du monde
  - Raison: incoherence de generation, maintenance complexe, rollback difficile
- Empiler des mods perf agressifs sans besoin mesure
  - Raison: gains incertains + risques de compat; utiliser `spark` d'abord pour profiler

## Plan de test par mod (checklist)
Appliquer a chaque mod candidat (staging d'abord):

1. Backup
- backup `world/`, `mods/`, `config/`

2. Boot technique
- serveur demarre sans crash
- pas d'erreurs de compat dans `latest.log`
- temps de demarrage acceptable

3. Validation gameplay Cobblemon
- connexion client OK
- combat/capture Cobblemon OK
- commandes/admin de base OK
- pas de regression UI majeure

4. Validation du mod
- `spark`: commandes repondent, profil capture possible
- `Flan`: claim spawn cree, interactions autorisees comme attendu
- `Chunky`: `chunky start/progress` fonctionne
- `Waystones`: pose/utilisation de waystone, teleport stable, client sync OK

5. Performance / logs
- verifier TPS/latence percue
- verifier absence d'exceptions repetees

6. Rollback
- suppression du mod testee (si applicable)
- restauration `mods/` + `config/` + monde si impact

## Decision finale proposee (ordre d'implementation)
Ordre recommande (coherent avec vos runbooks):

1. `spark` (diagnostic)
2. `Chunky` (pregen) + execution de pregen si nouveau monde/open world
3. `Flan` (protection spawn/village)
4. `Waystones` (si le groupe valide l'acceleration des trajets)
5. `Additional Structures` / autres changements worldgen uniquement sur nouveau monde

## Pack final exact recommande (style Better Minecraft utilitaire)
### Serveur (a installer dans `./data/mods`)
Mods deja couverts par scripts existants:
- `Chunky` -> `infra/mods-install-openworld.sh`
- `Flan` -> `infra/mods-install-openworld.sh`
- `Waystones` (+ `Balm`) -> `infra/mods-install-waystones.sh`

Nouveaux scripts ajoutes pour ce pack:
- `spark` -> `infra/mods-install-better-qol.sh`
- `Cardinal Components API` (dep requise de `Traveler's Backpack`) -> `infra/mods-install-better-qol.sh`
- `Traveler's Backpack` -> `infra/mods-install-better-qol.sh`
- `FallingTree` -> `infra/mods-install-better-qol.sh`
- `You're in Grave Danger (YIGD)` -> `infra/mods-install-better-qol.sh`

Versions pinnees (MC `1.21.1` / Fabric):
- `spark` -> `1.10.109-fabric`
- `Cardinal Components API` -> `6.1.3`
- `Traveler's Backpack` -> `1.21.1-10.1.33` (Fabric)
- `FallingTree` -> `1.21.1-1.21.1.11`
- `YIGD` -> `2.4.18` (Fabric)

### Client (chaque joueur)
Obligatoire si ces mods sont actifs cote serveur:
- `Waystones` (et `Balm` si le pack client ne l'a pas deja, mais il est deja dans le modpack officiel)
- `Traveler's Backpack`
- `YIGD`

Recommande (QoL Better Minecraft / tri auto des coffres):
- `Inventory Profiles Next (IPN)` -> tri auto coffres + inventaire
- `libIPN` (dependance IPN)
- `Fabric Language Kotlin` (dependance IPN)

Versions pinnees client-only (tri auto):
- `Inventory Profiles Next` -> `fabric-1.21.1-2.2.3`
- `libIPN` -> `fabric-1.21.1-6.6.2`
- `Fabric Language Kotlin` -> `1.13.9+kotlin.2.3.10`

Notes client:
- `IPN`, `libIPN`, `Fabric Language Kotlin` sont **client-only** (ne pas installer sur le serveur pour ce besoin).
- `FallingTree` peut rester serveur-only, mais installer le mod cote client peut ameliorer la coherence UX.
- Le modpack officiel contient deja `Fabric API` et `Mod Menu`.

### Commandes serveur recommandees (ordre)
```bash
./infra/mods-install-openworld.sh      # Chunky + Flan
./infra/mods-install-waystones.sh      # Waystones + Balm
./infra/mods-install-better-qol.sh     # spark + backpack + timber + YIGD
```

Vocal groupe retenu:
- Discord (externe au serveur) pour limiter la complexite reseau/ops.

## Notes d'implementation (repo)
- Inventaire genere par: `tools/mod_audit.py`
- Verification du pack serveur recommande: `tools/check_recommended_server_mods.py`
- Fichiers de sortie:
  - `audit/mods-current-inventory.csv`
  - `audit/mods-current-inventory.json`
  - `audit/recommended-server-mods-check.json` (si `--write`)
- Pour passer en "verite terrain" (serveur reel):

```powershell
py -3 tools/mod_audit.py --write --mods-dir .\data\mods
```

Puis verifier les logs du serveur (`./data/logs/latest.log` / `docker logs cobblemon`).

Controle du pack serveur recommande (jars manquants / hash mismatch / extras):

```powershell
py -3 tools/check_recommended_server_mods.py --write --mods-dir .\data\mods
```
