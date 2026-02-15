# Runbook: 2e Disque Pour Backups

## Situation actuelle (2026-02-12)
- Disque detecte: `/dev/sdb1` (NTFS, UUID `8E4E593B4E591CF1`)
- Les tentatives de montage ont bloque (`mount.ntfs-3g` en etat `D`), et `ntfsfix` indique que le volume est corrompu / qu'il faut lancer `chkdsk`.
- La ligne `fstab` a ete commentee pour eviter de nouveaux blocages au boot.

## Option A (conserver NTFS)
1. Redemarrer la machine (pour liberer les process bloques).
2. Re-tenter en lecture seule puis lecture/ecriture.
3. Si necessaire:
   - Brancher le disque sur Windows et lancer `chkdsk /f` sur la partition.
   - Desactiver "Fast Startup" / hibernation si le disque vient de Windows.

## Option B (recommande: disque dedie, format ext4)
Attention: ca efface le contenu de `/dev/sdb1`.

1. Reboot (recommande).
2. Formater:
   - `mkfs.ext4 -L mc_backups /dev/sdb1`
3. Monter de facon persistante (exemple):
   - `mkdir -p /mnt/backup2`
   - ajouter dans `/etc/fstab`:
     - `UUID=<uuid-ext4> /mnt/backup2 ext4 defaults,nofail 0 2`
   - `mount /mnt/backup2`
4. Configurer la copie:
   - `SECONDARY_BACKUP_DIR=/mnt/backup2/codex-cobblemon/backups` dans `.env`
   - lancer `./infra/backup-secondary.sh`
   - ajouter le cron `minecraft-backup-secondary`
