# Cobblemon Capture XP

Objectif: donner de l'XP au Pokemon de tete quand un joueur capture un Pokemon sauvage, comme dans les jeux principaux recents.

Etat de compatibilite verifie le 2026-03-03:
- Minecraft: `1.21.1`
- Cobblemon: `1.7.3`
- Loader: `Fabric`
- Mods serveur:
  - `Cobblemon Tim Core` -> `1.7.3-fabric-1.31.0`
  - `Cobblemon Capture XP` -> `1.7.3-fabric-1.3.0`

Important:
- pas de mod client a installer pour cette fonctionnalite
- les metadonnees Modrinth indiquent `client_side: unsupported`, `server_side: required` pour `Capture XP` et `Tim Core`

Reglage production actuel:
- au 2026-03-04, le serveur est regle sur `multiplier: 2.0`

Sources:
- `https://modrinth.com/mod/cobblemon-capture-xp`
- `https://modrinth.com/mod/cobblemon-tim-core`
- `https://github.com/timinc-cobble/cobblemon-capturexp`

## 1. Backup
Depuis `<MC_PROJECT_DIR>`:

```bash
./infra/backup.sh
```

## 2. Arret propre
```bash
./infra/stop.sh
```

## 3. Installation
```bash
./infra/mods-install-capturexp.sh
```

Option si vous voulez un multiplicateur different a l'installation:

```bash
CAPTUREXP_MULTIPLIER=1.5 ./infra/mods-install-capturexp.sh
```

Ce script:
- installe `timcore-fabric-1.7.3-1.31.0.jar`
- installe `capturexp-fabric-1.7.3-1.3.0.jar`
- cree `./data/config/capture_xp.json5` si le fichier n'existe pas encore

## 4. Configuration
Fichier gere:
- `./data/config/capture_xp.json5`

Commande dediee:

```bash
./infra/capturexp-configure.sh 1.5
```

Le fichier ecrit ressemble a:

```json
{
  "multiplier": 1.5
}
```

Comportement:
- `1.0` = gain normal
- `2.0` = double l'XP
- `0.5` = moitie de l'XP
- `0` = desactive l'XP a la capture sans desinstaller le mod

Note:
- d'apres la source upstream actuelle, `multiplier` est l'unique option exposee

## 5. Verification avant demarrage
```bash
python3 ./tools/check_recommended_server_mods.py --script infra/mods-install-capturexp.sh
```

Attendu:
- `expected=2`
- `missing=0`
- `hash_mismatch=0`

## 6. Redemarrage
```bash
./infra/start.sh
```

## 7. Smoke test gameplay
- entrer avec un client Cobblemon 1.7.3 standard
- placer en premier de l'equipe un Pokemon qui n'est pas deja au niveau max
- capturer un Pokemon sauvage
- verifier que le Pokemon de tete gagne de l'XP

## 8. Rollback rapide
1. Arreter le serveur:
```bash
./infra/stop.sh
```
2. Supprimer les jars ajoutes:
```bash
rm -f ./data/mods/timcore-fabric-1.7.3-1.31.0.jar
rm -f ./data/mods/capturexp-fabric-1.7.3-1.3.0.jar
```
3. Redemarrer:
```bash
./infra/start.sh
```
