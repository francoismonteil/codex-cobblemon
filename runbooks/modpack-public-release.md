# Modpack Public Release (CurseForge + Modrinth)

Objectif: produire et publier un modpack client public, en artefacts doubles:
- Modrinth `.mrpack`
- CurseForge `.zip` avec `manifest.json`

## Source de verite

- Catalogue lock: `modpack/public-client-pack/catalog.lock.json`
- Source packwiz: `modpack/public-client-pack/packwiz/`
- Overrides pack: `modpack/public-client-pack/overrides/`

Le lock est derive de:
- `manifest.Lydu1ZNo.json` (base Cobblemon officielle)
- `runbooks/client-pack-recommended.md` (ajouts clients recommandes)

## Commandes

Windows PowerShell:

```powershell
./modpack/release.ps1 validate
./modpack/release.ps1 build --version 1.0.0
./modpack/release.ps1 publish-checklist --version 1.0.0
```

Linux/macOS:

```bash
./modpack/release.sh validate
./modpack/release.sh build --version 1.0.0
./modpack/release.sh publish-checklist --version 1.0.0
```

Commande de maintenance lock (interne):

```powershell
py ./tools/modpack_release.py sync-lock
```

## Politique bloquante

Avant build:
- Tous les mods doivent etre resolus sur Modrinth **et** CurseForge.
- IDs/version/file IDs/hashes doivent etre pinnes dans le lock.
- Aucun `unresolved` n'est accepte.
- Les exclusions d'intersection sont explicites dans `catalog.lock.json` (`warnings`).

## Sorties attendues

Pour `--version X.Y.Z`:
- `dist/X.Y.Z/modrinth/*.mrpack`
- `dist/X.Y.Z/curseforge/*.zip`
- `dist/X.Y.Z/notes/changelog.fr-en.md`
- `dist/X.Y.Z/notes/publish-checklist.md`

## Publication manuelle

1. Uploader le `.mrpack` sur Modrinth.
2. Uploader le `.zip` CurseForge.
3. Utiliser le meme numero de version et le meme changelog FR/EN.
4. Verifier installation sur launcher Modrinth et CurseForge/Prism.
5. Verifier connexion serveur sans `version mismatch`.
