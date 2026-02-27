# Installation du pack de mods serveur recommande (Cobblemon + QoL)

Objectif: installer le pack serveur recommande "Better Minecraft utilitaire" sans changer le modpack Cobblemon officiel.

Pack concerne (serveur):
- `Chunky` + `Flan`
- `Waystones` (+ `Balm`)
- `spark`
- `Traveler's Backpack` (+ `Cardinal Components API`)
- `FallingTree`
- `YIGD`
- `Storage Drawers`
- `Tom's Simple Storage Mod`

Client (a communiquer aux joueurs, separement):
- voir `runbooks/client-pack-recommended.md`

## Pre-conditions
- Fenetre de maintenance annoncee (downtime)
- Acces au repo sur le serveur (`<MC_PROJECT_DIR>`)
- Backups fonctionnels
- Espace disque suffisant pour backup + nouveaux jars

## 1. Backup (obligatoire)
Depuis `<MC_PROJECT_DIR>`:

```bash
./infra/backup.sh
```

Verifications minimales:
- l'archive apparait dans `./backups/`
- taille non nulle

## 2. Arreter le serveur proprement
```bash
./infra/stop.sh
```

Option (si vous utilisez vos alias de conversation):
- `mc stop`

## 3. Installer les mods serveur recommandes
Ordre recommande (dependencies/ops):

```bash
./infra/mods-install-openworld.sh      # Chunky + Flan
./infra/mods-install-waystones.sh      # Waystones + Balm
./infra/mods-install-better-qol.sh     # spark + backpack + timber + YIGD
./infra/mods-install-storage.sh        # Storage Drawers + Tom's Storage
```

Notes:
- `Balm` est deja present dans le modpack officiel, mais le script `Waystones` repinne explicitement la version.
- Aucun mod voice chat integre n'est installe (choix: Discord externe).

## 4. Verification des jars installes (avant demarrage)
```bash
./infra/mods-check-recommended.sh
```

Ce script verifie:
- jars manquants
- `sha256` mismatch
- jars extras (informational)

Rapport ecrit dans:
- `audit/recommended-server-mods-check.json`

Criteres OK avant demarrage:
- `missing=0`
- `hash_mismatch=0`

## 5. Redemarrer le serveur
```bash
./infra/start.sh
```

Option alias:
- `mc start`

## 6. Validation post-demarrage (smoke tests)
### Logs
```bash
./infra/logs.sh
sed -n '1,240p' ./data/logs/latest.log 2>/dev/null || true
```

Verifier:
- pas de crash au boot
- pas de `Incompatible mods`
- pas de `NoClassDefFoundError`

### Gameplay rapide (1 joueur)
- connexion client OK (modpack 1.7.3 + pack client recommande)
- ouverture inventaire / coffre OK
- tri auto de coffre OK (IPN cote client)
- `Waystones` visible/utilisable (si posee)
- mort de test / tombe YIGD (optionnel en staging)
- craft + placement d'un `Drawer` OK
- terminal Tom's Storage relie a des coffres/drawers OK

### Performance rapide
- lancer un profil si besoin:
```bash
./infra/mc.sh "spark healthreport"
```

## 7. Rollback rapide (si probleme)
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

## Checklist courte (operateur)
- [ ] Backup cree
- [ ] Serveur stoppe proprement
- [ ] `mods-install-openworld.sh` execute
- [ ] `mods-install-waystones.sh` execute
- [ ] `mods-install-better-qol.sh` execute
- [ ] `mods-install-storage.sh` execute
- [ ] `mods-check-recommended.sh` -> `missing=0`, `hash_mismatch=0`
- [ ] Serveur redemarre sans erreur
- [ ] Smoke test client OK (IPN / backpack / YIGD / Waystones / Storage)
