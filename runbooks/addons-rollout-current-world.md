# Rollout addons Cobblemon - monde actuel

Objectif: deployer les nouveaux addons Cobblemon en plusieurs maintenances courtes, sans reset de saison et sans melanger plusieurs changements a risque dans la meme fenetre.

Statut courant:
- lot `1` (`Cobblemon Pokenav`) deploye et valide le `2026-03-04`
- lot `2` (`APS Trophies`) deploye et valide le `2026-03-04`
- lot `3` (`Cobblemon Quick Battle`) deploye et valide le `2026-03-04`
- lot `4` (`Cobbleloots`) deploye et valide le `2026-03-04`
- lot `5` (`Raid Dens`) deploye le `2026-03-04`, actuellement en observation longue
- lot `6` (`Blue's Cobblemon Utilities`) deploye le `2026-03-04`, actuellement en observation restreinte
- journal d'execution: `audit/addons-rollout-journal.md`

Base actuelle incluse dans le checker:
- `Chunky`, `Flan`
- `Waystones`, `Balm`
- `spark`, `Traveler's Backpack`, `FallingTree`, `YIGD`
- `Storage Drawers`, `Tom's Storage`
- lots progressifs deja deployes:
  - `Macaw's Furniture`
  - `Resourceful Lib`, `Handcrafted`
  - `Moonlight Lib`, `Supplementaries`
  - `YUNG's API`, `YUNG's Better Strongholds`
  - `Cristel Lib`, `Towns and Towers`

Contrainte:
- un seul lot par maintenance
- backup obligatoire avant installation
- verification cumulative obligatoire avant redemarrage
- observation reelle avant le lot suivant

## Ordre retenu

1. `./infra/mods-install-addon-lot1-pokenav.sh`
2. `./infra/mods-install-addon-lot2-aps-trophies.sh`
3. `./infra/mods-install-addon-lot3-quick-battle.sh`
4. `./infra/mods-install-addon-lot4-cobbleloots.sh`
5. `./infra/mods-install-addon-lot5-raiddens.sh`
6. `./infra/mods-install-addon-lot6-blues-utilities.sh`
7. `./infra/mods-install-addon-lot7-gacha-machine.sh`
8. `./infra/mods-install-addon-lot8-shiny-cookie.sh`

Verification cumulative:

```bash
./infra/mods-check-addons-rollout.sh --through-lot 1
```

Remplacer `1` par le lot courant (`2` a `8`).

Rapports JSON:
- `audit/addons-server-mods-check-lot1.json`
- ...
- `audit/addons-server-mods-check-lot8.json`

Criteres OK:
- `missing=0`
- `hash_mismatch=0`

## Procedure standard par lot

### 1. Preparation

1. annoncer la maintenance
2. verifier que personne n'est connecte
3. lancer un backup:

```bash
./infra/backup.sh
```

4. capturer l'etat avant changement:

```bash
./infra/status.sh
./infra/mc.sh "spark tps"
tail -n 200 ./data/logs/latest.log
```

### 2. Arret

```bash
./infra/stop.sh
```

### 3. Installation du lot

Exemple lot 1:

```bash
./infra/mods-install-addon-lot1-pokenav.sh
./infra/mods-check-addons-rollout.sh --through-lot 1
```

Exemple lot 6:

```bash
./infra/mods-install-addon-lot6-blues-utilities.sh
./infra/mods-check-addons-rollout.sh --through-lot 6
```

### 4. Redemarrage

```bash
./infra/start.sh
```

### 5. Validation technique

Verifier:

```bash
./infra/status.sh
sed -n '1,260p' ./data/logs/latest.log 2>/dev/null || true
```

Chercher en priorite:
- `Mod resolution failed`
- `Incompatible mods found`
- `NoClassDefFoundError`
- `Mixin apply failed`
- `Failed to load datapacks`
- crash loop / restart loop

Puis:

```bash
./infra/mc.sh "spark tps"
```

### 6. Observation

- respecter la fenetre d'observation du lot
- ne pas enchainer deux lots dans la meme maintenance

## Validation specifique par lot

## Lot 1 - Cobblemon Pokenav

Commande:

```bash
./infra/mods-install-addon-lot1-pokenav.sh
./infra/mods-check-addons-rollout.sh --through-lot 1
```

Validation:
- connexion client avec `cobblenav-fabric-2.2.5.jar`
- item / interface Pokenav utilisable
- pas de conflit visible avec `Xaero's Minimap` / `Xaero's World Map`
- pas de spam log

Observation:
- `1` vraie session minimum
- `24h` avant le lot suivant

Rollback rapide:
- retirer `cobblenav-fabric-2.2.5.jar`

## Lot 2 - APS Trophies

Commande:

```bash
./infra/mods-install-addon-lot2-aps-trophies.sh
./infra/mods-check-addons-rollout.sh --through-lot 2
```

Validation:
- attribution d'un trophee de test
- pose / affichage / conservation du trophee
- connexion d'un joueur sans `Catch Indicator` OK
- connexion d'un joueur avec `Catch Indicator` OK

Note client:
- `Catch Indicator` reste un ajout client-only recommande, non bloquant

Observation:
- `1` vraie session minimum
- `24h`

Rollback rapide:
- retirer `aps_trophies-1.21.1-fabric-1.1.1.jar`
- gerer manuellement les trophees deja distribues si besoin

## Lot 3 - Cobblemon Quick Battle

Commande:

```bash
./infra/mods-install-addon-lot3-quick-battle.sh
./infra/mods-check-addons-rollout.sh --through-lot 3
```

Validation:
- combat rapide fonctionnel
- combat classique non regresse
- capture apres combat OK
- pas de duplication ou soft-lock
- pas de desync visible client/serveur

Observation:
- `2` vraies sessions minimum
- `48h`

Rollback rapide:
- retirer `cobblemon_quick_battle-fabric-1.2.5.jar`

## Lot 4 - Cobbleloots

Commande:

```bash
./infra/mods-install-addon-lot4-cobbleloots.sh
./infra/mods-check-addons-rollout.sh --through-lot 4
```

Validation:
- generation de points/balls de loot dans de nouveaux chunks
- coherence des recompenses
- absence d'erreurs repetees dans les tables/configs
- pas de regression du loot vanilla ou Cobblemon existant

Observation:
- `2` vraies sessions minimum
- `72h`

Rollback:
- retrait du jar si rejet rapide
- si des loots ont deja circule, accepter qu'un vrai retour arriere demande `restore.sh`

## Lot 5 - Raid Dens

Commande:

```bash
./infra/mods-install-addon-lot5-raiddens.sh
./infra/mods-check-addons-rollout.sh --through-lot 5
```

Validation:
- `GeckoLib` et `Raid Dens` presents cote client
- nouvelles dens dans des chunks non critiques
- entree/sortie d'un raid
- recompenses coherentes
- pas de corruption de chunk
- pas de spam logs lie a generation / entites

Observation:
- `3` vraies sessions minimum
- `72h a 7 jours`

Signaux de rollback immediat:
- crash ou fuite d'erreurs sur les raids
- generation de dens manifestement corrompue
- pertes de progression ou recompenses anormales

Rollback:
- si rejet tres rapide: retirer `geckolib-fabric-1.21.1-4.8.4.jar` et `cobblemonraiddens-fabric-0.8.1+1.21.1.jar`
- si les dens ont deja ete generees et jouees: preferer `./infra/restore.sh`

Note:
- `Raid Dens Design` reste bloque tant que la source officielle exacte n'est pas epinglee

## Lot 6 - Blue's Cobblemon Utilities

Commande:

```bash
./infra/mods-install-addon-lot6-blues-utilities.sh
./infra/mods-check-addons-rollout.sh --through-lot 6
```

Validation:
- `./infra/mc.sh "datapack list enabled"` montre `file/blues-cobblemon-utilities-4.0.0.zip`
- test des fonctions explicitement autorisees
- desactivation/test de coupure des usages futurs si besoin
- pas d'erreur datapack apres `reload` / reboot

Regle d'exposition:
- `admins + 1 joueur volontaire` au demarrage
- `48h` d'essai ferme

Rollback:
- retirer le zip du datapack
- pour revenir a l'etat gameplay exact d'avant: `./infra/restore.sh backups/<backup>.tar.gz`

## Lot 7 - CobbledGacha

Commande:

```bash
./infra/mods-install-addon-lot7-gacha-machine.sh
./infra/mods-check-addons-rollout.sh --through-lot 7
```

Validation:
- machine placable / utilisable
- recompenses delivrees sans erreur
- pas de crafting public avant validation du lot
- test de retrait propre apres usage minimal

Regle d'exposition:
- distribution initiale admin-only
- `48h` max avant decision

Rollback:
- retrait du jar si rejet immediat
- si des recompenses ont deja circule: restaurer le backup si retour arriere integral requis

## Lot 8 - Cobblemon: Shiny Cookie

Commande:

```bash
./infra/mods-install-addon-lot8-shiny-cookie.sh
./infra/mods-check-addons-rollout.sh --through-lot 8
```

Validation:
- obtention admin-only
- utilisation controlee sur un Pokemon de test
- verification du chemin de retrait
- decision binaire a la fin du lot:
  - conserver
  - retirer

Regle d'exposition:
- pas d'ouverture publique si la decision n'est pas immediate

Rollback:
- retirer `shinycookie-fabric-0.0.1.jar`
- effet deja applique a un Pokemon non reversible automatiquement

## Rollback standard

1. arreter le serveur:

```bash
./infra/stop.sh
```

2. si retrait rapide suffisant:
- retirer le jar ou le zip du lot

3. si un vrai retour arriere est requis:

```bash
./infra/restore.sh backups/<backup-file>.tar.gz
```

4. redemarrer:

```bash
./infra/start.sh
```

5. suspendre le lot suivant

## References

- versions verrouillees: `audit/addons-compat-lock-20260304.md`
- pack client actuel: `runbooks/client-pack-recommended.md`
- pack client de ce rollout: `runbooks/client-pack-addons-rollout.md`
- baseline serveur historique: `runbooks/server-mods-recommended-install.md`
- rollout progressif deja realise: `runbooks/mods-progressive-rollout.md`
