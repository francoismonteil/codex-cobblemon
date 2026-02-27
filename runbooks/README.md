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
- `runbooks/chatops.md`: admin depuis le chat Minecraft (ChatOps, sans plugin/mod).
- `runbooks/client-setup.md`: installer le bon client/modpack (eviter les version mismatch).
- `runbooks/storage-rollout.md`: templates de communication (maintenance/online/rollback) pour le rollout des mods de stockage.
- `runbooks/friends-guide.md`: infos a partager aux amis (connexion, install, whitelist/op via scripts).
- `runbooks/discord-bot.md`: bot Discord pour whitelist self-service (slash commands).
- `runbooks/alerting.md`: alertes (webhook Discord) pour monitoring.
- `runbooks/restart-policy.md`: restart quotidien safe + alertes.
- `runbooks/secondary-disk.md`: preparer un 2e disque pour stocker les backups.
- `runbooks/openworld-village.md`: open world (spawn village naturel + border + pregen + protection spawn).
- `runbooks/server-mods-recommended-install.md`: installation du pack de mods serveur recommande (QoL + verification + rollback court).
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
