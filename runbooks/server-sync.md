# Server Sync

Objectif: aligner le serveur avec le workspace local sans transformer le serveur en depot git.

## Principe

Le script `./infra/deploy-server.ps1` pousse un ensemble controle de fichiers depuis le workspace local vers `<MC_PROJECT_DIR>`:
- racine: `README.md`, `.env.example`, `AGENTS.md`, `docker-compose.yml`, `docker-compose.pregen.yml`, `manifest.Lydu1ZNo.json`
- dossiers geres: `infra/`, `runbooks/`, `datapacks/`, `tools/`, `admin-web/`, `modpack/`

Le script:
- lit `runbooks/site.local.md`
- pousse le contenu sur le serveur via SSH/SCP
- supprime les fichiers en trop uniquement dans le perimetre gere (sauf `-NoDeleteExtra`)
- retire `runbooks/site.local.md` du serveur si present
- peut creer un backup distant du perimetre gere avant sync (`-CreateRemoteBackup`)
- peut verifier l'etat du service Minecraft apres sync (`-VerifyService`)

Ce que le script **ne touche pas**:
- `.env`
- `data/`
- `backups/`
- `downloads/`
- `logs/`
- `worlds/`

## Prerequis

- `runbooks/site.local.md` renseigne avec:
  - `MC_SERVER_HOST`
  - `MC_SSH_USER`
  - `MC_PROJECT_DIR`
  - `SSH_KEY_MAIN`
- `ssh`, `scp`, `tar` disponibles sur le poste admin Windows

## Dry-run

```powershell
./infra/deploy-server.ps1 -DryRun
```

Affiche la liste des fichiers geres sans rien pousser.

## Sync standard

```powershell
./infra/deploy-server.ps1
```

Usage recommande:
- avant un changement de procedure/runbook
- apres ajout/modification d'un script `infra`
- apres modification d'un datapack versionne

## Sync avec backup distant + verification service

```powershell
./infra/deploy-server.ps1 -CreateRemoteBackup -VerifyService
```

Usage recommande:
- apres une serie de changements infra/runbooks/datapacks
- avant une fenetre d'exploitation ou de test sur le serveur
- quand tu veux un filet de securite avant nettoyage du perimetre gere

## Sync sans suppression des extras distants

```powershell
./infra/deploy-server.ps1 -NoDeleteExtra
```

Utile si tu veux pousser des mises a jour sans nettoyer des fichiers distants possiblement conserves a la main.

## Verification service seule pendant un deploy

Par defaut, le script ne controle pas l'etat du conteneur Minecraft apres sync. Pour rendre ce controle bloquant:

```powershell
./infra/deploy-server.ps1 -VerifyService
```

Le nom du conteneur verifie vient de `MC_SERVICE_NAME` dans `runbooks/site.local.md`, sinon `cobblemon`.

## Verification rapide post-sync

```bash
cd <MC_PROJECT_DIR>
./infra/mc.sh "datapack list enabled"
docker inspect cobblemon --format 'status={{.State.Status}} health={{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}'
```

## Limite

Le serveur reste un repertoire de travail synchronise, pas un checkout git.  
La source de verite reste le workspace local.
