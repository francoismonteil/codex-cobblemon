# Client Pack Recommande (etat actuel du serveur)

Objectif: donner aux joueurs la liste exacte des mods client actuellement requis/recommandes pour rejoindre le serveur en production.

## Base (obligatoire)
- Minecraft: `1.21.1`
- Modpack: `Cobblemon Official Modpack [Fabric] 1.7.3`

Important:
- Desactiver les auto-updates du launcher/modpack
- Garder exactement les versions attendues par le serveur

## Mods client a ajouter (recommandes)
### Gameplay / compat serveur (si installes sur le serveur)
- `Waystones` -> `21.1.27+fabric-1.21.1`
- `Traveler's Backpack` -> `1.21.1-10.1.33` (Fabric)
- `You're in Grave Danger (YIGD)` -> `2.4.18` (Fabric)
- `Storage Drawers` -> `1.21.1-13.11.4` (Fabric)
- `Tom's Simple Storage Mod` -> `1.21-2.3.0-fabric`
- `Macaw's Furniture` -> `3.4.1`
- `Resourceful Lib` -> `3.0.12`
- `Handcrafted` -> `4.0.3`
- `Moonlight Lib` -> `1.21-2.29.18-fabric`
- `Supplementaries` -> `1.21-3.5.25-fabric`
- `Cristel Lib` -> `3.0.3`
- `Towns and Towers` -> `1.13.7`

### QoL "Better Minecraft" (tri auto coffres / inventaire)
- `Inventory Profiles Next (IPN)` -> `fabric-1.21.1-2.2.3`
- `libIPN` (dependance IPN) -> `fabric-1.21.1-6.6.2`
- `Fabric Language Kotlin` (dependance IPN) -> `1.13.9+kotlin.2.3.10`

### QoL optionnel (confort)
- `FallingTree` -> `1.21.1-1.21.1.11`
  - Peut fonctionner serveur-only, mais l'installer cote client ameliore la coherence UX.

## Deja dans le modpack officiel (ne pas reinstaller)
- `Balm` (dependance de Waystones)
- `Fabric API`
- `Mod Menu`
- `Xaero's Minimap` / `Xaero's World Map`
- `JEI` / `EMI`

## A ne PAS installer cote client pour ce setup
(mods serveur/admin uniquement)
- `spark`
- `Chunky`
- `Flan`
- `YUNG's API`
- `YUNG's Better Strongholds`

## Notes worldgen
- `YUNG's Better Strongholds` est actif cote serveur mais ne demande pas de mod client.
- `Towns and Towers` est traite comme requis cote joueurs pour simplifier le support, meme si le projet est annonce comme client optionnel.

## Vocal retenu
- Pas de mod voix integre
- Utiliser Discord (vocal externe)

## Checklist rapide (joueur)
1. Installer le modpack officiel `Cobblemon Official Modpack [Fabric] 1.7.3`
2. Ajouter les mods ci-dessus (versions exactes)
3. Verifier que le launcher reste en `Minecraft 1.21.1`
4. Lancer une fois le jeu pour verifier qu'il n'y a pas de `version mismatch`

## Si erreur "Version mismatch"
- Supprimer la mauvaise version du mod
- Reinstaller la version exacte listee ici
- Verifier que le launcher n'a pas auto-mis a jour le mod
