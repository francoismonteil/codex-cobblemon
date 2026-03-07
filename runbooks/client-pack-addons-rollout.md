# Pack client pour le rollout addons Cobblemon

Objectif: donner aux joueurs la liste exacte des ajouts clients a appliquer lot par lot, en complement du pack client deja actif sur le serveur.

Base obligatoire:
- Minecraft `1.21.1`
- `Cobblemon Official Modpack [Fabric] 1.7.3`
- pack client actuel du serveur: voir `runbooks/client-pack-recommended.md`

Important:
- desactiver les auto-updates
- ne mettre a jour le client qu'au moment ou le lot serveur correspondant est annonce

## Lot 1

Ajouter:
- `Cobblemon Pokenav` -> `2.2.5`

## Lot 2

Ajouter:
- `APS Trophies` -> `1.1.1`

Option recommande, non bloquante:
- `Catch Indicator` -> `1.4.1`

## Lot 3

Ajouter:
- `Cobblemon Quick Battle` -> `1.2.5`

## Lot 4

Ajouter:
- `Cobbleloots` -> `2.2.2`

## Lot 5

Ajouter:
- `GeckoLib` -> `4.8.4`
- `Cobblemon Raid Dens` -> `0.8.1+1.21.1`

## Lot 6

Ajouter:
- rien de plus cote client

Note:
- `Blue's Cobblemon Utilities` est deploye cote serveur comme datapack zip
- le projet annonce `client optional`, mais aucun jar client n'est requis dans ce rollout

## Lot 7

Ajouter:
- `Farmer's Delight Refabricated` -> `3.2.5`

## Lot 8

Ajouter:
- `Architectury API` -> `13.0.8+fabric`
- `Bookshelf` -> `21.1.81`
- `Prickle` -> `21.1.11`
- `Botany Pots` -> `21.1.41`
- `Cobblemon Botany Pots` -> `1.0.1`

## Lot 9

Ajouter:
- `CobbledGacha` -> `3.0.2`

## Lot 10

Ajouter:
- `Cobblemon: Shiny Cookie` -> `0.0.1`

## Checklist joueur

1. garder le modpack officiel en `Minecraft 1.21.1`
2. garder le pack client actuel du serveur
3. ajouter uniquement les mods du lot annonce
4. relancer le launcher
5. verifier qu'il n'y a pas de `version mismatch`

## Si erreur de version

- supprimer la mauvaise version du mod
- reinstaller la version exacte
- verifier que le launcher n'a pas auto-mis a jour le jar

## References

- baseline client actuelle: `runbooks/client-pack-recommended.md`
- rollout serveur associe: `runbooks/addons-rollout-current-world.md`
- versions verrouillees: `audit/addons-compat-lock-20260304.md`
