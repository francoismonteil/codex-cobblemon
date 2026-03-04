# Addons compat lock - 2026-03-04

Base cible:
- Minecraft `1.21.1`
- Loader `Fabric`
- Cobblemon `1.7.3`

Objectif:
- verrouiller les versions, URLs, SHA256 et dependances des addons et lots de saison
- distinguer clairement ce qui est deployable sur le monde actuel de ce qui doit rester sur une future saison

## Monde actuel - lots serveur

### Lot 1 - Cobblemon Pokenav
- Addon: `Cobblemon Pokenav`
- Track: `current_world`
- Artifact kind: `mod`
- Version: `2.2.5`
- Source primaire: `https://modrinth.com/mod/cobblemon-pokenav/version/VjtSuwwW`
- Download URL: `https://cdn.modrinth.com/data/bI8Nt3uA/versions/VjtSuwwW/cobblenav-fabric-2.2.5.jar`
- SHA256: `3fd669b03f152ab9f5ed3da71b25ea6b95944876367e6e289948bf8a1f159333`
- Dependencies: `Fabric API`, `Cobblemon`
- Side requirement: `both`
- Removal difficulty: `easy`
- Rollback note: `jar removal is enough for a fast rollback`

### Lot 2 - APS Trophies
- Addon: `APS Trophies`
- Track: `current_world`
- Artifact kind: `mod`
- Version: `1.1.1`
- Source primaire: `https://modrinth.com/mod/aps-trophies/version/LA6Nn9cA`
- Download URL: `https://cdn.modrinth.com/data/ZmP6jlh0/versions/LA6Nn9cA/aps_trophies-1.21.1-fabric-1.1.1.jar`
- SHA256: `17e55ba120ffc80105ad29cd7e34ab4f3a9112a349e6f8f49c995f1029d942bf`
- Dependencies: `none`
- Side requirement: `both`
- Removal difficulty: `easy_to_medium`
- Rollback note: `jar removal is enough; already-awarded trophies remain to be cleaned manually if needed`

### Lot 2 - Catch Indicator
- Addon: `Catch Indicator`
- Track: `client_optional_only`
- Artifact kind: `mod`
- Version: `1.4.1`
- Source primaire: `https://modrinth.com/mod/catch-indicator/version/Kuy7LGYe`
- Download URL: `https://cdn.modrinth.com/data/tpTcu2PM/versions/Kuy7LGYe/catchindicator-fabric-1.4.1.jar`
- SHA256: `a3524b4f4a445a53866e2d6248d47019bc4916e76f2894839309874861f5b6a7`
- Dependencies: `none`
- Side requirement: `client_only`
- Removal difficulty: `easy`
- Rollback note: `no server rollback required`

### Lot 3 - Cobblemon Quick Battle
- Addon: `Cobblemon Quick Battle`
- Track: `current_world`
- Artifact kind: `mod`
- Version: `1.2.5`
- Source primaire: `https://modrinth.com/mod/cobblemon-quick-battle/version/dTaK0vNR`
- Download URL: `https://cdn.modrinth.com/data/55fHndP6/versions/dTaK0vNR/cobblemon_quick_battle-fabric-1.2.5.jar`
- SHA256: `5f230102ae4575b615204ee8ce71e289dbbfc4113d3ebf2996a5464f5693501b`
- Dependencies: `none`
- Side requirement: `both`
- Removal difficulty: `easy`
- Rollback note: `jar removal is enough during the short trial window`

### Lot 4 - Cobbleloots
- Addon: `Cobbleloots`
- Track: `current_world`
- Artifact kind: `mod`
- Version: `2.2.2`
- Source primaire: `https://modrinth.com/mod/cobbleloots/version/wbVVXjGi`
- Download URL: `https://cdn.modrinth.com/data/kcudYghD/versions/wbVVXjGi/cobbleloots-fabric-2.2.2.jar`
- SHA256: `f3944ddabc08842300000b0866b685a88c16034a1f003c03fdc931b1a1dc50ce`
- Dependencies: `Fabric API`, `Cobblemon`
- Side requirement: `both`
- Removal difficulty: `medium`
- Rollback note: `jar removal is easy, but accepted loot already injected into the economy remains unless a world backup is restored`

### Lot 5 - GeckoLib
- Addon: `GeckoLib`
- Track: `current_world_dependency`
- Artifact kind: `mod`
- Version: `4.8.4`
- Source primaire: `https://modrinth.com/mod/geckolib/version/3GjkJptS`
- Download URL: `https://cdn.modrinth.com/data/8BmcQJ2H/versions/3GjkJptS/geckolib-fabric-1.21.1-4.8.4.jar`
- SHA256: `905df8858ed4aa3a5c2a845b7c83bf1e3274c348d8e623269e7e245a3e2e647d`
- Dependencies: `none`
- Side requirement: `required_by_raid_dens`
- Removal difficulty: `tied_to_parent_lot`
- Rollback note: `remove together with Raid Dens if the lot is rejected`

### Lot 5 - Cobblemon Raid Dens
- Addon: `Cobblemon Raid Dens`
- Track: `current_world`
- Artifact kind: `mod`
- Version: `0.8.1+1.21.1`
- Source primaire: `https://modrinth.com/mod/cobblemonraiddens/version/viyx90Qw`
- Download URL: `https://cdn.modrinth.com/data/GebWh45l/versions/viyx90Qw/cobblemonraiddens-fabric-0.8.1%2B1.21.1.jar`
- SHA256: `2dfc086e3a9ce8621d5c3a55202baeec416cde1819f2b8653b61a7ea3641bf5f`
- Dependencies: `GeckoLib`, `Fabric API`, `Cobblemon`
- Side requirement: `both`
- Removal difficulty: `medium`
- Rollback note: `jar removal is possible only for a fast rejection; once dens are generated and used, prefer restore.sh with the pre-lot backup`

### Lot 6 - Blue's Cobblemon Utilities
- Addon: `Blue's Cobblemon Utilities`
- Track: `current_world`
- Artifact kind: `datapack_archive`
- Version: `4.0.0`
- Source primaire: `https://modrinth.com/mod/blues-cobblemon-utilities/version/9kqOqPlg`
- Download URL: `https://cdn.modrinth.com/data/HMbKoqXZ/versions/9kqOqPlg/Blue%27s%20Cobblemon%20Utilities.zip`
- SHA256: `6295c2e17be8ed92cb9a6668ab221afde613736329103edc37a97083a3f4f037`
- Dependencies: `Cobblemon`
- Side requirement: `server_required_client_optional`
- Removal difficulty: `easy_infra`
- Rollback note: `the datapack zip can be removed cleanly, but gameplay changes already applied to Pokemon are not expected to auto-revert`
- Implementation note: `Modrinth project metadata says mod, but the selected 1.21.1 artifact is published with loader=datapack`

### Lot 7 - Farmer's Delight Refabricated
- Addon: `Farmer's Delight Refabricated`
- Track: `current_world`
- Artifact kind: `mod`
- Version: `3.2.5`
- Source primaire: `https://modrinth.com/mod/farmers-delight-refabricated/version/Sddkv0PO`
- Download URL: `https://cdn.modrinth.com/data/7vxePowz/versions/Sddkv0PO/FarmersDelight-1.21.1-3.2.5+refabricated.jar`
- SHA256: `023bb687d0453dec1ad5de17c4d55a750bb0144046d6ad37022f99ef0a39fa4d`
- Dependencies: `Fabric API`
- Side requirement: `both`
- Removal difficulty: `easy_to_medium`
- Rollback note: `jar removal is enough for a fast rollback, but already-placed blocks and crafted items remain in the world`

### Lot 8 - Architectury API
- Addon: `Architectury API`
- Track: `current_world_dependency`
- Artifact kind: `mod`
- Version: `13.0.8+fabric`
- Source primaire: `https://modrinth.com/mod/architectury-api/version/Wto0RchG`
- Download URL: `https://cdn.modrinth.com/data/lhGA9TYQ/versions/Wto0RchG/architectury-13.0.8-fabric.jar`
- SHA256: `10cbbb6f5f96a2f1853b0cc68428424cec8903409517b299ff02350756b6399d`
- Dependencies: `none`
- Side requirement: `required_by_cobblemon_botany_pots`
- Removal difficulty: `tied_to_parent_lot`
- Rollback note: `remove together with the full Botany Pots stack if lot 8 is rejected`

### Lot 8 - Bookshelf
- Addon: `Bookshelf`
- Track: `current_world`
- Artifact kind: `mod`
- Version: `21.1.81`
- Source primaire: `https://modrinth.com/mod/bookshelf-lib/version/kpkjWpa5`
- Download URL: `https://cdn.modrinth.com/data/uy4Cnpcm/versions/kpkjWpa5/bookshelf-fabric-1.21.1-21.1.81.jar`
- SHA256: `df2dd3a3e75f2dbf56baf9bdb6cc0007f9c0efb0f2b2067f047ddf98ea1b49d8`
- Dependencies: `none`
- Side requirement: `both`
- Removal difficulty: `tied_to_parent_lot`
- Rollback note: `remove together with the full Botany Pots stack if lot 8 is rejected`

### Lot 8 - Prickle
- Addon: `Prickle`
- Track: `current_world`
- Artifact kind: `mod`
- Version: `21.1.11`
- Source primaire: `https://modrinth.com/mod/prickle/version/Ef7P6Rb7`
- Download URL: `https://cdn.modrinth.com/data/aaRl8GiW/versions/Ef7P6Rb7/prickle-fabric-1.21.1-21.1.11.jar`
- SHA256: `d6d639078aecb72770f287d8253e4634114e2536ac9a2ad6ec5f442eb27dd07f`
- Dependencies: `none`
- Side requirement: `both`
- Removal difficulty: `tied_to_parent_lot`
- Rollback note: `remove together with the full Botany Pots stack if lot 8 is rejected`

### Lot 8 - Botany Pots
- Addon: `Botany Pots`
- Track: `current_world`
- Artifact kind: `mod`
- Version: `21.1.41`
- Source primaire: `https://modrinth.com/mod/botany-pots/version/Bz6dkTjV`
- Download URL: `https://cdn.modrinth.com/data/U6BUTZ7K/versions/Bz6dkTjV/botanypots-fabric-1.21.1-21.1.41.jar`
- SHA256: `14dd5d079030e2b6dfda629a8c48255c82c55ba01e15e15810b1aaaf30110bc4`
- Dependencies: `Bookshelf`, `Prickle`
- Side requirement: `both`
- Removal difficulty: `medium`
- Rollback note: `jar removal is possible, but already-placed pots, soils and automation layouts remain in the world`

### Lot 8 - Cobblemon Botany Pots
- Addon: `Cobblemon Botany Pots`
- Track: `current_world`
- Artifact kind: `mod`
- Version: `1.0.1`
- Source primaire: `https://www.curseforge.com/minecraft/mc-mods/cobblemon-botany-pots`
- Download URL: `https://mediafilez.forgecdn.net/files/7074/619/cobblemon_pots-fabric-1.0.1.jar`
- SHA256: `38884fdf8d968b54c258f15a37316e3d04a35f83a267d4bde3b964d8f1ba076b`
- Dependencies: `Cobblemon`, `Botany Pots`, `Architectury API`
- Side requirement: `both`
- Removal difficulty: `medium`
- Rollback note: `remove with the full Botany Pots stack; harvested items already produced stay in circulation unless a backup is restored`

## Future season / new world

### Lot S1 - Cobblemon: Mega Showdown
- Addon: `Cobblemon: Mega Showdown`
- Track: `next_season`
- Artifact kind: `mod`
- Version: `1.6.12+1.7.3+1.21.1`
- Source primaire: `https://modrinth.com/mod/cobblemon-mega-showdown/version/FgMP7Nw8`
- Download URL: `https://cdn.modrinth.com/data/SszvX85I/versions/FgMP7Nw8/mega_showdown-fabric-1.6.12%2B1.7.3%2B1.21.1.jar`
- SHA256: `f07d873a24ca99da21bad095e27278e31f5421995a3f30d0b4e74b9fe1c1436e`
- Dependencies: `Accessories`, `Architectury API`, `owo-lib`, `Fabric API`, `Cobblemon`
- Side requirement: `both`
- Removal difficulty: `medium_to_hard`
- Rollback note: `treat as a season-level system change; do not inject into the current live world`

### Lot S2 - Legendary Monuments
- Addon: `Cobblemon: Legendary Monuments`
- Track: `next_season`
- Artifact kind: `mod`
- Version: `7.8`
- Source primaire: `https://modrinth.com/mod/legendary-monuments/version/kSVEEVIv`
- Download URL: `https://cdn.modrinth.com/data/m6RyHSbV/versions/kSVEEVIv/LegendaryMonuments-7.8.jar`
- SHA256: `5507d1f3f5c9d4afe1db3aac7ae20f88b491daaeb3aa7edc150cca8ad6fefcfc`
- Dependencies: `Chipped`, `Accessories`, `CobbleFurnies`, `TerraBlender`, `Mega Showdown`, `Cobblemon`
- Side requirement: `both`
- Removal difficulty: `hard`
- Rollback note: `do not deploy on the current world; reserve for a fresh season with staging and chunk pregen`

### Lot S3 - Fierce Competition (mod)
- Addon: `Cobblemon: Fierce Competition`
- Track: `next_season`
- Artifact kind: `mod`
- Version: `beta4p2+mod`
- Source primaire: `https://modrinth.com/mod/cbmn-fierce/version/O62c7MA9`
- Download URL: `https://cdn.modrinth.com/data/dldXzOEF/versions/O62c7MA9/cbmn-fierce-beta4p2.jar`
- SHA256: `0dcc5195d202a5e5c8cab903f93490941c463a229afd7ca5492d6169dcfaee06`
- Dependencies: `Cobblemon`
- Side requirement: `server_required_client_optional`
- Removal difficulty: `hard`
- Rollback note: `keep for a season staging world only`

### Lot S3 - Fierce Competition (datapack)
- Addon: `Cobblemon: Fierce Competition`
- Track: `next_season`
- Artifact kind: `datapack_archive`
- Version: `beta4p2`
- Source primaire: `https://modrinth.com/mod/cbmn-fierce/version/2YnUqtxX`
- Download URL: `https://cdn.modrinth.com/data/dldXzOEF/versions/2YnUqtxX/FierceCompetition_BETA4-part2.zip`
- SHA256: `51fee01a1116062051e02d3e062842cce5b6859627cfc76fdb3cca3807dd286e`
- Dependencies: `Cobblemon`
- Side requirement: `server_required_client_optional`
- Removal difficulty: `hard`
- Rollback note: `treat as a paired mod+datapack season experiment, not as a mid-season live patch`

## Blocked / unresolved

### Farmer's Delight (mainline CurseForge project)
- Addon: `Farmer's Delight`
- Track: `blocked`
- Artifact kind: `mod`
- Version: `not_selected`
- Source primaire: `https://www.curseforge.com/minecraft/mc-mods/farmers-delight`
- Download URL: `not_selected`
- SHA256: `not_selected`
- Dependencies: `n/a`
- Side requirement: `forge_or_neoforge_only`
- Removal difficulty: `n/a`
- Rollback note: `do not use on this Fabric server; use Farmer's Delight Refabricated instead`

### Tomtaru's Cobblemon & Farmer's Delight Tweaks
- Addon: `Tomtaru's Cobblemon & Farmer's Delight Tweaks`
- Track: `blocked`
- Artifact kind: `mod`
- Version: `2.0.3`
- Source primaire: `https://www.curseforge.com/minecraft/mc-mods/tomtarus-cobblemon-farmers-delight-tweaks`
- Download URL: `not_selected`
- SHA256: `not_selected`
- Dependencies: `Farmer's Delight`, `Cobblemon`
- Side requirement: `neoforge_only_on_1.21.1`
- Removal difficulty: `n/a`
- Rollback note: `exclude from the active Fabric plan until an official Fabric 1.21.1 build exists`

### CobbleCuisine
- Addon: `CobbleCuisine`
- Track: `blocked`
- Artifact kind: `mod`
- Version: `2.0.1-1.7-rc1`
- Source primaire: `https://www.curseforge.com/minecraft/mc-mods/cobblecuisine`
- Download URL: `not_selected`
- SHA256: `not_selected`
- Dependencies: `Cobblemon`, `MidnightLib`
- Side requirement: `both`
- Removal difficulty: `n/a`
- Rollback note: `excluded from the active plan because the current Cobblemon 1.7.x line is published as alpha/rc`

### CobbleFoods
- Addon: `CobbleFoods`
- Track: `blocked`
- Artifact kind: `mod`
- Version: `1.3.3-1.20.1`
- Source primaire: `https://www.curseforge.com/minecraft/mc-mods/cobblefoods`
- Download URL: `not_selected`
- SHA256: `not_selected`
- Dependencies: `Cobblemon`
- Side requirement: `both`
- Removal difficulty: `n/a`
- Rollback note: `exclude from the active plan until a Fabric 1.21.1 build exists`

### CobbledGacha
- Addon: `CobbledGacha`
- Track: `deferred`
- Artifact kind: `mod`
- Version: `3.0.2`
- Source primaire: `https://modrinth.com/mod/cobbledgacha/version/Ifh7vKgZ`
- Download URL: `not_selected`
- SHA256: `not_selected`
- Dependencies: `none`
- Side requirement: `both`
- Removal difficulty: `medium`
- Rollback note: `removed from the active 8-lot plan when lots 7 and 8 were realigned toward safer farming content`

### Cobblemon: Shiny Cookie
- Addon: `Cobblemon: Shiny Cookie`
- Track: `deferred`
- Artifact kind: `mod`
- Version: `0.0.1`
- Source primaire: `https://modrinth.com/mod/cobblemon-shiny-cookie/version/YIna1pKh`
- Download URL: `not_selected`
- SHA256: `not_selected`
- Dependencies: `none`
- Side requirement: `both`
- Removal difficulty: `easy_infra`
- Rollback note: `removed from the active 8-lot plan when lots 7 and 8 were realigned toward safer farming content`

### Raid Dens Design
- Addon: `Raid Dens Design`
- Track: `blocked`
- Artifact kind: `unknown_pending_validation`
- Version: `unknown`
- Source primaire: `missing`
- Download URL: `unknown`
- SHA256: `unknown`
- Dependencies: `unknown`
- Side requirement: `unknown_pending_validation`
- Removal difficulty: `unknown`
- Rollback note: `do not implement until the exact official project page and artifact are pinned`
