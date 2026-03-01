# Worlds (plusieurs maps)

Par defaut, un serveur Minecraft "vanilla/Fabric" n'a qu'un seul monde actif a la fois (dossier `./data/world`).

Ce repo supporte:
- une bibliotheque de mondes `./worlds/<name>` (pour en avoir plusieurs installes)
- un switch "propre" (stop, backup, copy, start) pour changer de map quand tu veux

Si tu viens de modifier localement les scripts de gestion de mondes, un runbook associe ou des datapacks a embarquer avec une map, synchronise d'abord le serveur:

```powershell
./infra/deploy-server.ps1 -CreateRemoteBackup -VerifyService
```

Reference: `runbooks/server-sync.md`

## Installer plusieurs maps
Tu telecharges les zips (CurseForge/ailleurs), puis tu les importes dans la bibliotheque.

Sur le serveur:
```bash
cd <MC_PROJECT_DIR>
mkdir -p downloads
```

Upload depuis Windows:
```powershell
scp -i <SSH_KEY_MAIN> "C:\chemin\map1.zip" <MC_SSH_USER>@<MC_SERVER_HOST>:<MC_PROJECT_DIR>/downloads/
scp -i <SSH_KEY_MAIN> "C:\chemin\map2.zip" <MC_SSH_USER>@<MC_SERVER_HOST>:<MC_PROJECT_DIR>/downloads/
```

Import (sans toucher le monde actif):
```bash
./infra/world-import-zip.sh ./downloads/map1.zip johto
./infra/world-import-zip.sh ./downloads/map2.zip autre
```

Lister:
```bash
./infra/worlds-list.sh
```

## Activer une map (switch)
```bash
./infra/world-switch.sh johto
```

Optionnel: sauvegarder aussi le monde actif dans la bibliotheque avant switch:
```bash
./infra/world-switch.sh johto --save-current-as current_before_johto
```

## Peut-on avoir plusieurs maps actives en meme temps ?
Pas dans une seule instance Fabric "standard".
Deux options si tu veux du simultane:
- lancer 2 serveurs (2 conteneurs) sur 2 ports differents
- ou passer sur une stack plugin (Paper/Bukkit) avec un plugin multi-world (pas compatible Cobblemon Fabric tel quel)

## Securite (maps telechargees)
- Garde `enable-command-block=false` tant qu'on n'a pas besoin de command blocks.
- Evite d'OP des gens sur une map non verifiee.
- Certaines maps ont des datapacks/scripts: teste d'abord en local/staging si tu veux etre prudent.
