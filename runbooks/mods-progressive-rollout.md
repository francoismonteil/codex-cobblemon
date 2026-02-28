# Rollout progressif des mods additionnels (monde actuel)

> Statut: deploiement realise le 2026-02-28.
> Ce runbook reste utile comme historique operatoire et comme procedure de rollback par lot.

Objectif: deployer les 5 mods additionnels sur le monde actuel en plusieurs vagues, du plus faible impact au plus fort impact worldgen.

## Portee

Ce runbook **n'ecrase pas** le pack serveur recommande deja en production. Il ajoute un second flux:
- baseline actuelle: `Chunky`, `Flan`, `Waystones`, `spark`, `Traveler's Backpack`, `YIGD`, `Storage Drawers`, `Tom's Storage`
- lots additionnels:
  1. `Macaw's Furniture`
  2. `Handcrafted` + `Resourceful Lib`
  3. `Supplementaries` + `Moonlight Lib`
  4. `YUNG's API` + `YUNG's Better Strongholds`
  5. `Cristel Lib` + `Towns and Towers`

Contrainte cle:
- `Towns and Towers` reste le lot final, car il touche la generation future des villages sur un monde ou `acm_pokemon_worldgen` et `additionalstructures_1211` sont deja actifs.

## Ordre de deploiement

1. `./infra/mods-install-progressive-lot1-macaws-furniture.sh`
2. `./infra/mods-install-progressive-lot2-handcrafted.sh`
3. `./infra/mods-install-progressive-lot3-supplementaries.sh`
4. `./infra/mods-install-progressive-lot4-yungs-strongholds.sh`
5. `./infra/mods-install-progressive-lot5-towns-and-towers.sh`

Chaque lot doit etre:
- backupe
- deploye
- smoke teste
- observe en session reelle

Ne pas enchainer deux lots dans la meme maintenance.

## Verification cumulative des jars

Avant le redemarrage, verifier le contenu attendu de `./data/mods` avec:

```bash
./infra/mods-check-progressive.sh --through-lot 1
```

Remplacer `1` par le lot courant (`2`, `3`, `4`, `5`).

Rapport JSON ecrit dans:
- `audit/progressive-server-mods-check-lot1.json`
- ...
- `audit/progressive-server-mods-check-lot5.json`

Criteres OK:
- `missing=0`
- `hash_mismatch=0`

## Procedure standard par lot

### 1. Preparation

1. annoncer la maintenance aux joueurs
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
./infra/mods-install-progressive-lot1-macaws-furniture.sh
./infra/mods-check-progressive.sh --through-lot 1
```

Exemple lot 4:

```bash
./infra/mods-install-progressive-lot4-yungs-strongholds.sh
./infra/mods-check-progressive.sh --through-lot 4
```

### 4. Redemarrage

```bash
./infra/start.sh
```

### 5. Validation post-demarrage

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
- crash loop / restart loop

Puis:

```bash
./infra/mc.sh "spark tps"
```

### 6. Observation

Garder le lot en observation pendant au moins une vraie session de jeu avant le lot suivant.

## Validation specifique par lot

## Lot 1 - Macaw's Furniture

Commande:

```bash
./infra/mods-install-progressive-lot1-macaws-furniture.sh
./infra/mods-check-progressive.sh --through-lot 1
```

Validation en jeu:
- craft/placement d'une chaise
- craft/placement d'une table
- verification simple dans une claim Flan et hors claim

## Lot 2 - Handcrafted + Resourceful Lib

Commande:

```bash
./infra/mods-install-progressive-lot2-handcrafted.sh
./infra/mods-check-progressive.sh --through-lot 2
```

Validation en jeu:
- chaise
- table
- etagere
- verification des recettes

## Lot 3 - Supplementaries + Moonlight Lib

Commande:

```bash
./infra/mods-install-progressive-lot3-supplementaries.sh
./infra/mods-check-progressive.sh --through-lot 3
```

Validation en jeu:
- jarre
- corde
- signpost/panneau
- un bloc fonctionnel leger
- verifier l'absence de bruit log `Moonlight`

## Lot 4 - YUNG's Better Strongholds + YUNG's API

Commande:

```bash
./infra/mods-install-progressive-lot4-yungs-strongholds.sh
./infra/mods-check-progressive.sh --through-lot 4
```

Validation supplementaire:

```bash
./infra/mc.sh "locate structure minecraft:stronghold"
```

Puis, apres confirmation du boot:
- explorer un stronghold non encore visite
- verifier absence de lag severe
- verifier absence d'erreurs logs repetees

Note client:
- `YUNG's Better Strongholds` est serveur requis / client non requis

## Lot 5 - Towns and Towers + Cristel Lib

Commande:

```bash
./infra/mods-install-progressive-lot5-towns-and-towers.sh
./infra/mods-check-progressive.sh --through-lot 5
```

Validation supplementaire:
- seulement dans de nouveaux chunks
- localiser plusieurs villages neufs
- verifier que les elements ACM attendus restent presents ou coherents
- verifier qu'Additional Structures continue a apparaitre

Signaux de rollback immediat:
- villages casses
- routes incoherentes
- structures mal posees
- disparition manifeste du comportement attendu de `acm_pokemon_worldgen`
- erreurs worldgen repetees

En cas de doute:
- rollback

## Rollback

1. arreter le serveur:

```bash
./infra/stop.sh
```

2. restaurer le backup:

```bash
./infra/restore.sh backups/<backup-file>.tar.gz
```

3. redemarrer:

```bash
./infra/start.sh
```

4. suspendre le lot suivant

## References

- pack serveur actuel: `runbooks/server-mods-recommended-install.md`
- pack client progressif: `runbooks/client-pack-progressive-rollout.md`
- baseline client actuelle: `runbooks/client-pack-recommended.md`
