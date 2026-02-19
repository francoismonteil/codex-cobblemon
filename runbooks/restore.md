# Runbook: Restauration

## Procedure standard (Linux/SSH)
1) Arreter le serveur:
```bash
cd <MC_PROJECT_DIR>
./infra/stop.sh
```
2) Faire un backup avant restauration:
```bash
./infra/backup.sh
```
3) Choisir l'archive dans `backups/`.
4) Restaurer:
```bash
./infra/restore.sh backups/backup-YYYYMMDD-HHMMSS.tar.gz
```
5) Redemarrer:
```bash
./infra/start.sh
```
6) Valider via `runbooks/restore-test.md`.

## Variante Windows (PowerShell local)
```powershell
./infra/stop.ps1
./infra/backup.ps1
./infra/restore.ps1 -Archive backups/backup-YYYYMMDD-HHMMSS.zip
./infra/start.ps1
```
