# Backups Cobblemon

## Strategie
- Objectif: sauvegarder les donnees persistantes du serveur Fabric (bind mount `data/`).
- Le backup est obligatoire avant toute modification ou restauration.
- Les archives sont nommees par horodatage et contiennent un manifeste de hachage.

## Structure
- `backups/backup-YYYYMMDD-HHMMSS.zip`
- `backups/` est le point unique de stockage local des archives.
- Le manifeste `manifest.json` est inclus dans chaque archive.

## Commandes de haut niveau
- Executer une sauvegarde: `powershell -File infra/backup.ps1`
- Restaurer une archive: `powershell -File infra/restore.ps1 -Archive backups/backup-YYYYMMDD-HHMMSS.zip`
