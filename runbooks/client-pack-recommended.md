# Client Pack Recommande (Cobblemon + QoL "Better Minecraft")

Objectif: donner aux joueurs une liste courte de mods client a ajouter au modpack officiel, sans doublons inutiles.

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
