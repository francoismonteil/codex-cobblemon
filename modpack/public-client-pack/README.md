# Public Client Pack

Ce dossier contient la source de verite du modpack public client.

- `catalog.lock.json`: lock machine-readable (Modrinth + CurseForge, IDs et hashes)
- `packwiz/`: source packwiz generee depuis le lock
- `overrides/`: fichiers de config/client a embarquer dans les exports

Generation lock:

```powershell
py ./tools/modpack_release.py sync-lock
```
