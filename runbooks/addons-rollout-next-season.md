# Addons Cobblemon - prochaine saison / nouveau monde

Objectif: documenter les addons volontairement exclus du monde actuel, mais retenus comme candidats de saison apres staging.

Regle:
- aucun de ces lots n'est deploye sur la prod actuelle
- staging obligatoire sur copie de monde ou nouveau monde
- pre-generation d'une zone de test avant validation

## Lot S1 - Mega Showdown

Artifact principal:
- `mega_showdown-fabric-1.6.12+1.7.3+1.21.1.jar`

Version source:
- `https://modrinth.com/mod/cobblemon-mega-showdown/version/FgMP7Nw8`

Dependencies a embarquer cote clients + serveur:
- `Accessories`
- `Architectury API`
- `owo-lib`
- `Fabric API`
- `Cobblemon`

Pourquoi saison seulement:
- changement systemique majeur de meta
- nouvelles attentes joueurs sur objets/formes/combats
- retrait plus couteux qu'un simple lot QoL

Validation minimale:
- mega evolution fonctionnelle en combat
- zero regression sur combat Cobblemon standard
- pas de desync client/serveur
- verification des objets / formes / triggers associes

## Lot S2 - Legendary Monuments

Artifact principal:
- `LegendaryMonuments-7.8.jar`

Version source:
- `https://modrinth.com/mod/legendary-monuments/version/kSVEEVIv`

Dependencies a embarquer:
- `Mega Showdown`
- `Chipped`
- `Accessories`
- `CobbleFurnies`
- `TerraBlender`
- `Cobblemon`

Pourquoi saison seulement:
- dependance forte a `Mega Showdown`
- impact structure/worldgen trop fort pour la saison actuelle
- cout de rollback eleve une fois les chunks generes

Validation minimale:
- monuments generes dans des chunks neufs
- absence de conflits majeurs avec le reste de la stack worldgen
- progression/recompenses coherentes

## Lot S3 - Fierce Competition

Artifacts retenus:
- mod: `cbmn-fierce-beta4p2.jar`
- datapack: `FierceCompetition_BETA4-part2.zip`

Versions source:
- mod: `https://modrinth.com/mod/cbmn-fierce/version/O62c7MA9`
- datapack: `https://modrinth.com/mod/cbmn-fierce/version/2YnUqtxX`

Pourquoi saison seulement:
- projet encore beta
- touche trainers/structures/combat
- rollback sale si on l'injecte sur un monde deja avance

Validation minimale:
- generation de trainers/structures sur chunks neufs
- combats stables
- pas de logs repetes
- pas de blocage de progression

## Procedure de staging recommandee

1. creer une copie de monde ou un nouveau monde de test
2. installer le lot cible et ses dependances
3. pre-generer une zone de validation
4. valider logs + performances + contenu
5. ouvrir une session multi courte
6. decider:
   - `retenu pour saison`
   - `rejete`

## Non retenu / bloque

### Raid Dens Design

Statut:
- `bloque`

Raison:
- source officielle exacte non epinglee
- impossible de verrouiller proprement version, dependances et strategie de retrait

Condition de debloquage:
- fournir le lien officiel primaire exact
- revalider compatibilite `1.21.1 / Fabric`
- definir si c'est un mod, datapack, resourcepack ou un simple pack de structures/configs
