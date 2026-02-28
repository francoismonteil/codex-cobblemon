# Notes d'exploitation (persistantes)

Derniere mise a jour: 2026-02-28

## Capacite serveur (snapshot)
- Snapshot materiel/OS/reseau: `runbooks/server-capacity.md`
  - Dernier releve: 2026-02-13T06:24:50-06:00

## Cible serveur
- Host/IP: `<MC_SERVER_HOST>` (voir `runbooks/site.local.md`)
- OS: Linux (compte admin utilise: `<MC_SSH_USER>`)
- Repertoire projet: `<MC_PROJECT_DIR>` (example: `/home/linux/codex-cobblemon`)

## Acces SSH
- Commande: `ssh <MC_SSH_USER>@<MC_SERVER_HOST>`
- Commande recommandee (cle dediee): `ssh -i <SSH_KEY_MAIN> <MC_SSH_USER>@<MC_SERVER_HOST>`
- Commande secours (break-glass): `ssh -i <SSH_KEY_EMERGENCY> <MC_SSH_USER>@<MC_SERVER_HOST>`
- Auth actuelle: cle SSH uniquement
- Cle privee locale (poste admin): `<SSH_KEY_MAIN>` (chemin Windows, voir `runbooks/site.local.md`)
- Cle privee locale secours: `<SSH_KEY_EMERGENCY>`
- Cle publique installee sur serveur: `~/.ssh/authorized_keys`
- Fingerprint cle admin: `<SSH_KEY_MAIN_FINGERPRINT>`
- Fingerprint cle secours: `<SSH_KEY_EMERGENCY_FINGERPRINT>`
- Verification 2026-02-11:
  - connexion par cle OK
  - connexion par cle secours OK
  - connexion par mot de passe SSH bloquee

## Service Minecraft
- Stack: Docker Compose
- Service: `cobblemon`
- Port jeu: `25565/tcp`
- Verification faite le 2026-02-28:
  - conteneur en execution
  - port `25565` en ecoute
  - log `Done (...)! For help, type "help"`

## Mods actifs en production (2026-02-28)
- Baseline utilitaire/gameplay:
  - `Chunky`
  - `Flan`
  - `Waystones`
  - `Balm`
  - `spark`
  - `Traveler's Backpack`
  - `Cardinal Components API`
  - `FallingTree`
  - `YIGD`
  - `Storage Drawers`
  - `Tom's Simple Storage Mod`
- Ajouts decoratifs / monde:
  - `Macaw's Furniture`
  - `Resourceful Lib`
  - `Handcrafted`
  - `Moonlight Lib`
  - `Supplementaries`
  - `YUNG's API`
  - `YUNG's Better Strongholds`
  - `Cristel Lib`
  - `Towns and Towers`

## Datapacks / packs serveur actifs (2026-02-28)
- Monde:
  - `file/acm_pokemon_worldgen`
  - `file/additionalstructures_1211`
- Mods exposes comme packs:
  - `betterstrongholds`
  - `handcrafted`
  - `mcwfurnitures`
  - `moonlight`
  - `supplementaries`
  - `supplementaries:generated_pack`
  - `t_and_t`
  - `t_and_t:resources/t_and_t_waystones_patch`

## Validation recente des ajouts (2026-02-28)
- Lots 1 a 5 deployes sur le monde actuel.
- Verification jars:
  - `./infra/mods-check-progressive.sh --through-lot 5`
  - resultat attendu/observe: `expected=20 ok=20 missing=0 hash_mismatch=0`
- Perf apres deploiement:
  - TPS ~ `20.0`
- Validation worldgen minimale:
  - `betterstrongholds:stronghold` localisable
  - `minecraft:village_plains` localisable
- Risque residuel a surveiller:
  - coherence de `Towns and Towers` sur de nouveaux chunks/villages en coexistence avec `acm_pokemon_worldgen`

## Profil performance applique (objectif 4 joueurs)
- Date d'application: 2026-02-11
- Memoire Java: `MEMORY=4608M`
- Flags JVM: `USE_AIKAR_FLAGS=true`
- Parametres `data/server.properties`:
  - `max-players=4`
  - `view-distance=8`
  - `simulation-distance=7`
  - `sync-chunk-writes=false`
  - `network-compression-threshold=512`
  - `entity-broadcast-range-percentage=90`
  - `spawn-protection=0`
  - `max-tick-time=120000`

## Pare-feu
- UFW actif
- Regles ouvertes:
  - `22/tcp` (SSH, limite au LAN `<LAN_CIDR>`)
  - `25565/tcp` (Minecraft)

## Durcissement SSH applique (2026-02-11)
- Fichier: `/etc/ssh/sshd_config.d/99-minecraft-hardening.conf`
- Parametres:
  - `PasswordAuthentication no`
  - `PubkeyAuthentication yes`
  - `PermitRootLogin no`
  - `KbdInteractiveAuthentication no`
  - `ChallengeResponseAuthentication no`
  - `AuthenticationMethods publickey`

## Anti-veille applique (2026-02-11)
- Objectif: garder le serveur actif meme ecran gele/capot ferme.
- Fichiers:
  - `/etc/systemd/logind.conf.d/99-headless-server.conf`
  - `/etc/systemd/sleep.conf.d/99-no-sleep.conf`
- Parametres:
  - `HandleLidSwitch=ignore`
  - `HandleLidSwitchExternalPower=ignore`
  - `HandleLidSwitchDocked=ignore`
  - `HandleSuspendKey=ignore`
  - `HandleHibernateKey=ignore`
  - `HandlePowerKey=ignore`
  - `IdleAction=ignore`
  - `AllowSuspend=no`
  - `AllowHibernation=no`
  - `AllowSuspendThenHibernate=no`
  - `AllowHybridSleep=no`
- Cibles systemd masquees:
  - `sleep.target`
  - `suspend.target`
  - `hibernate.target`
  - `hybrid-sleep.target`

## Commandes d'admin courantes
Depuis le serveur, dans `<MC_PROJECT_DIR>`:

```bash
./infra/start.sh
./infra/stop.sh
./infra/logs.sh
./infra/backup.sh
./infra/restore.sh backups/backup-YYYYMMDD-HHMMSS.tar.gz
```

## Redemarrage quotidien automatique
- Methode active: `cron` utilisateur `linux`
- Horaire: tous les jours a `05:00` (heure locale serveur)
- Entree crontab:
  - `0 5 * * * cd <MC_PROJECT_DIR> && <MC_PROJECT_DIR>/infra/safe-restart.sh >> <MC_PROJECT_DIR>/logs/minecraft-daily-restart.log 2>&1 # minecraft-daily-restart`
- Log d'execution:
  - `<MC_PROJECT_DIR>/logs/minecraft-daily-restart.log`

## Monitoring / Alerting leger
- Script: `<MC_PROJECT_DIR>/infra/monitor.sh`
- Cron: toutes les 5 minutes (utilisateur `linux`)
  - `*/5 * * * * cd <MC_PROJECT_DIR> && <MC_PROJECT_DIR>/infra/monitor.sh >> <MC_PROJECT_DIR>/logs/minecraft-monitor-cron.log 2>&1 # minecraft-monitor`
- Fichier metriques:
  - `<MC_PROJECT_DIR>/logs/minecraft-monitor.log`
- Webhook optionnel via `.env`:
  - `MONITOR_WEBHOOK_URL=...`

## Coordonnees importantes (monde actuel)
- Spawn monde: `400 80 -1488`
- Pokecenter "village kit" (healer+PC, exterieur village):
  - healer: `397 80 -1489`
  - pc: `398 80 -1489`
  - welcome cache (baril stocke): `397 80 -1488`
- Pokecenter prefab (decorated), rectangle snap (blocs): `x=420..428`, `z=-1510..-1500`, `y=70`
  - healer: `426 71 -1505`
  - pc: `426 71 -1504`

## Backups
- Dossier: `<MC_PROJECT_DIR>/backups`
- Dernier backup valide observe: `backup-20260228-072820.tar.gz`

## Actions recommandees (securite)
1) Changer immediatement le mot de passe du compte `linux`.
2) Sauvegarder les 2 cles privees (admin + secours) dans un coffre (et definir un plan de rotation).
3) Documenter qui detient la cle secours et dans quelles conditions elle peut etre utilisee.
