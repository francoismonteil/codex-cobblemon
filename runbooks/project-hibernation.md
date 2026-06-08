# Project Hibernation

Last updated: 2026-06-08

Objectif: laisser le workspace dans un etat lisible avant une pause longue.

## Etat Git attendu

- Branche: `main`
- Base distante: `origin/main`
- Les fichiers locaux ignores peuvent rester presents sans etre synchronises:
  - `.env`
  - `runbooks/site.local.md`
  - `.idea/`
  - `downloads/`
  - `dist/`
  - `logs/`
  - `backups/`
  - caches Python / pytest
- Les rapports JSON generes par les audits de logs/stabilite sont ignores; conserver en git les syntheses Markdown relues.

## Source de verite de reprise

Lire dans cet ordre:

1. `runbooks/assistant-context.md`
2. `runbooks/ops-notes.md`
3. `runbooks/project-hibernation.md`
4. `runbooks/infra-commands.md`
5. `runbooks/academy-dimension.md` seulement si le chantier Academy reprend

## Etat operationnel connu

- La production documentee reste le monde Cobblemon courant.
- Les valeurs reelles d'acces serveur ne doivent pas etre commits; elles restent dans `runbooks/site.local.md` et `.env`.
- Le dernier etat d'exploitation detaille est dans `runbooks/ops-notes.md`.
- Avant toute action distante apres la pause, verifier d'abord:

```bash
./infra/status.sh
./infra/logs.sh
./infra/backup.sh
```

Puis, si des scripts/runbooks/datapacks ont change localement:

```powershell
./infra/deploy-server.ps1 -CreateRemoteBackup -VerifyService
```

## Chantier Academy

Etat: prepare mais non annonce comme rollout production.

- Source technique: `modpack/academy-v2/stack.lock.json`
- Runbook dimension: `runbooks/academy-dimension.md`
- Runbook pack client: `runbooks/client-pack-academy-v2.md`
- Datapack: `datapacks/acm_academy_dimension`
- Scripts:
  - `./infra/academy-compat-audit.py`
  - `./infra/academy-stack-install.sh`
  - `./infra/install-academy-dimension-datapack.sh`
  - `./infra/spawn-academy-portals.sh`

Decision actuelle:

- mode `fidelity_reduced`
- installer uniquement la stack compatible adjacente apres staging
- ne pas promettre le vrai Safari / houses / acceptance letters upstream tant que `StarAcademyMod` ne matche pas la base Cobblemon actuelle

Avant reprise Academy:

1. Rafraichir `downloads/academy-src` si present localement.
2. Executer `./infra/academy-compat-audit.py`.
3. Relire le rapport Markdown dans `audit/`.
4. Ne lancer aucun install serveur sans backup distant recent.

## A ne pas nettoyer sans verification

- `downloads/academy-src/`: source locale ignoree utile a l'audit Academy.
- `downloads/cobblemon-src/`: source locale ignoree utile aux audits/debugs Cobblemon.
- `backups/`: peut contenir des sauvegardes uniques non poussees.
- `runbooks/site.local.md`: contient les vraies valeurs locales.
- `.env`: contient la configuration locale.

## Reprise minimale

```powershell
git status --short --branch
py -3 -m pytest admin-web/tests infra/tests
```

Si les tests Python ne passent pas faute de dependances locales, installer d'abord les dependances documentees dans les sous-projets concernes au lieu de modifier le code.
