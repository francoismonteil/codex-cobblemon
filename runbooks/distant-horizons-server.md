# Distant Horizons cote serveur (Fabric)

Objectif: activer le support serveur Distant Horizons pour partager les LOD longues distances aux clients DH, sans rendre le mod obligatoire pour tous les joueurs.

## Important
- Les joueurs sans Distant Horizons peuvent toujours se connecter.
- Les joueurs avec Distant Horizons (version compatible) beneficient des LOD serveur.
- Ce flux n'est pas inclus dans le pack "mods serveur recommandes" de base; c'est un ajout optionnel.

## Pre-conditions
- Fenetre de maintenance annoncee.
- Acces SSH au serveur et repo present dans `<MC_PROJECT_DIR>`.
- Backup operationnel.

## 1. Backup (obligatoire)
```bash
./infra/backup.sh
```

## 2. Arret propre du serveur
```bash
./infra/stop.sh
```

## 3. Installer le mod serveur Distant Horizons
```bash
./infra/mods-install-distant-horizons.sh
```

## 4. Redemarrer le serveur
```bash
./infra/start.sh
```

## 5. Verification rapide
```bash
./infra/logs.sh
./infra/mc.sh "dh help"
```

A verifier:
- pas de crash au boot;
- pas d'erreur `Incompatible mods`;
- la commande `dh` repond (si op/admin).

## 6. Optionnel: pre-generation LOD DH
Quand la map/chunks est deja preparee (ex: Chunky), tu peux lancer la pre-generation DH pour remplir les LOD serveur:

```bash
./infra/mc.sh "dh pregen start minecraft:overworld 0 0 4000"
./infra/mc.sh "dh pregen status"
```

Adapte les coordonnees/rayon a votre zone utile.

## 7. Rollback rapide
1. Arreter le serveur:
```bash
./infra/stop.sh
```
2. Restaurer le backup:
```bash
./infra/restore.sh backups/<backup-file>.tar.gz
```
3. Redemarrer:
```bash
./infra/start.sh
```
