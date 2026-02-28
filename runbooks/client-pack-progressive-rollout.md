# Pack client pour le rollout progressif des mods additionnels

> Statut: rollout termine le 2026-02-28.
> Pour l'etat courant du serveur, la source de verite est maintenant `runbooks/client-pack-recommended.md`.

Objectif: donner aux joueurs les mods exacts a ajouter lot par lot, en complement du modpack officiel et du pack client actuel du serveur.

Base obligatoire:
- Minecraft `1.21.1`
- `Cobblemon Official Modpack [Fabric] 1.7.3`
- les mods deja requis par le serveur actuel, voir `runbooks/client-pack-recommended.md`

Important:
- desactiver les auto-updates
- installer exactement les versions ci-dessous
- ne mettre a jour le client qu'au moment ou le lot serveur correspondant est annonce en ligne

## Lot 1

Ajouter:
- `Macaw's Furniture` -> `3.4.1`

## Lot 2

Ajouter:
- `Resourceful Lib` -> `3.0.12`
- `Handcrafted` -> `4.0.3`

## Lot 3

Ajouter:
- `Moonlight Lib` -> `1.21-2.29.18-fabric`
- `Supplementaries` -> `1.21-3.5.25-fabric`

## Lot 4

Ajouter:
- rien de plus cote client

Note:
- `YUNG's Better Strongholds` est serveur requis / client non requis

## Lot 5

Ajouter:
- `Cristel Lib` -> `3.0.3`
- `Towns and Towers` -> `1.13.7`

Politique retenue:
- meme si `Towns and Towers` est annonce comme client optionnel, le serveur utilise une regle simple: les joueurs mettent a jour leur pack en meme temps que le lot serveur pour eviter les ambiguities de support

## Checklist joueur

1. garder le modpack officiel en `Minecraft 1.21.1`
2. ajouter uniquement les mods du lot annonce
3. relancer le launcher
4. verifier qu'il n'y a pas de `version mismatch`

## Si erreur de version

- supprimer la mauvaise version du mod
- reinstaller la version exacte
- verifier que le launcher n'a pas auto-mis a jour un des jars
