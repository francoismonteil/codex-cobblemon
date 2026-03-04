# Index runbooks

## Active
- `runbooks/assistant-context.md`: contexte operatoire de reference pour assistants.
- `runbooks/ops-notes.md`: etat actuel de production (source de verite operatoire).
- `runbooks/server-capacity.md`: snapshot capacites (CPU/RAM/disques/reseau/OS).
- `runbooks/ssh-setup.md`: setup initial d'une machine Linux en SSH.
- `runbooks/first-boot.md`: procedure de premier demarrage.
- `runbooks/crash-startup.md`: diagnostic en cas de crash au boot.
- `runbooks/lag-tps.md`: procedure de diagnostic/performance.
- `runbooks/ddns.md`: config d'un DNS dynamique (adresse stable) pour acces Internet.
- `runbooks/mc-admin.md`: commandes admin Minecraft (sans RCON).
- `runbooks/mc-admin-web.md`: panneau web prive d'administration Minecraft (sans RCON).
- `runbooks/chatops.md`: admin depuis le chat Minecraft (ChatOps, sans plugin/mod).
- `runbooks/client-setup.md`: installer le bon client/modpack (eviter les version mismatch).
- `runbooks/storage-rollout.md`: templates de communication (maintenance/online/rollback) pour le rollout des mods de stockage.
- `runbooks/friends-guide.md`: infos a partager aux amis (connexion, install, whitelist/op via scripts).
- `runbooks/discord-bot.md`: bot Discord pour whitelist self-service (slash commands).
- `runbooks/alerting.md`: alertes (webhook Discord) pour monitoring.
- `runbooks/pokedex-report.md`: generer un rapport detaille Pokedex serveur (seen/caught/temps de jeu) et publication Discord.
- `runbooks/server-sync.md`: aligner le serveur avec le workspace local via sync ciblee.
- `runbooks/restart-policy.md`: restart quotidien safe + alertes.
- `runbooks/secondary-disk.md`: preparer un 2e disque pour stocker les backups.
- `runbooks/openworld-village.md`: open world (spawn village naturel + border + pregen + protection spawn).
- `runbooks/server-mods-recommended-install.md`: installation du pack de mods serveur recommande (QoL + verification + rollback court).
- `runbooks/mods-progressive-rollout.md`: rollout progressif des mods additionnels sur le monde actuel, lot par lot.
- `runbooks/client-pack-progressive-rollout.md`: liste exacte des mods client a ajouter pour chaque lot progressif.
- `runbooks/addons-rollout-current-world.md`: rollout par lots des addons Cobblemon sur le monde actuel.
- `runbooks/addons-rollout-lot2-aps-trophies.md`: preparation operationnelle et templates de communication pour le lot 2 `APS Trophies`.
- `runbooks/addons-rollout-lot3-quick-battle.md`: preparation operationnelle et templates de communication pour le lot 3 `Cobblemon Quick Battle`.
- `runbooks/addons-rollout-lot4-cobbleloots.md`: preparation operationnelle et templates de communication pour le lot 4 `Cobbleloots`.
- `runbooks/addons-rollout-lot5-raiddens.md`: preparation operationnelle et templates de communication pour le lot 5 `Raid Dens`.
- `runbooks/addons-rollout-lot6-blues-utilities.md`: preparation operationnelle et templates de communication pour le lot 6 `Blue's Cobblemon Utilities`.
- `runbooks/addons-rollout-lot7-farmers-delight.md`: preparation operationnelle et templates de communication pour le lot 7 `Farmer's Delight Refabricated`.
- `runbooks/addons-rollout-lot8-botany-pots.md`: preparation operationnelle et templates de communication pour le lot 8 `Botany Pots + Cobblemon Botany Pots`.
- `runbooks/client-pack-addons-rollout.md`: liste exacte des ajouts client pour chaque lot d'addons Cobblemon.
- `runbooks/addons-rollout-next-season.md`: lots reserves a une future saison / nouveau monde.
- `runbooks/waystones-backfill-existing-villages.md`: poser des Waystones dans les villages deja generes d'une map existante (batch + resume).
- `runbooks/pokemon-worldgen.md`: datapack unique Pokemon worldgen (pokemart + pipeline structgen).
- `runbooks/additionalstructures-integration.md`: integration AS + ACM avec gate compatibilite stricte 1.21.1.
- `runbooks/worlds.md`: gerer plusieurs maps (bibliotheque + switch).
- `runbooks/johto-fr.md`: traduction FR (partielle) de la map Johto.
- `runbooks/progression.md`: progression badges (scoreboards) et commandes associees.
- `runbooks/restore.md`: procedure de restauration.
- `runbooks/restore-test.md`: checklist de validation post-restore.
- `runbooks/infra-commands.md`: index operationnel des scripts `infra/` (entrypoints + utilitaires).

## Legacy
- `runbooks/village-pokecenter-worldgen.md`: ancien flux Pokecenter par datapack dedie.
- `runbooks/windmill-worldgen-and-manual-plan.md`: ancien plan worldgen windmills.
- `runbooks/pokemon-worldgen-progress.md`: notes de progression historiques du chantier worldgen.
- `runbooks/spawn-city.md`: plan legacy de spawn "ville Pokemon" (non flux principal actuel).
- `runbooks/next-steps.md`: backlog historique, non prescriptif.

## Internal
- `runbooks/README.md`: index de classification des runbooks (active/legacy/internal).
- `runbooks/site.local.md.example`: template local (gitignore) pour valeurs sensibles/environnement.
