# Runbook: Lot 7 Farmer's Delight Refabricated

Objectif:
- preparer la maintenance du lot `7`
- disposer des messages de communication et de la checklist de test

Contexte cible:
- Minecraft `1.21.1`
- Cobblemon `1.7.3`
- lots precedents actifs:
  - `Cobblemon Pokenav 2.2.5`
  - `APS Trophies 1.1.1`
  - `Cobblemon Quick Battle 1.2.5`
  - `Cobbleloots 2.2.2`
  - `Raid Dens 0.8.1+1.21.1`
  - `Blue's Cobblemon Utilities 4.0.0`

Ajouts du lot:
- serveur:
  - `Farmer's Delight Refabricated 3.2.5`
- client obligatoire:
  - `Farmer's Delight Refabricated 3.2.5`

References:
- rollout principal: `runbooks/addons-rollout-current-world.md`
- pack client: `runbooks/client-pack-addons-rollout.md`
- verrou versions: `audit/addons-compat-lock-20260304.md`
- journal d'execution: `audit/addons-rollout-journal.md`

## Etat de preparation

Preflight deja valide:
- script lot 7 syntaxiquement OK:
  - `./infra/mods-install-addon-lot7-farmers-delight.sh`
- artefact `Farmer's Delight Refabricated 3.2.5` telechargeable et hash conforme

Preflight restant avant maintenance:
- verifier qu'aucun joueur n'est connecte
- prendre un backup pre-maintenance
- preparer au moins un joueur test avec `Farmer's Delight Refabricated 3.2.5`

## Template 1 - Annonce maintenance

```text
[MAINTENANCE SERVEUR COBBLEMON]

Maintenance prevue aujourd'hui a <HH:MM> (duree estimee: 15 a 20 min).
Objectif: deploiement du lot 7 addons:
- Farmer's Delight Refabricated 3.2.5

Ajout cote client pour rejoindre apres maintenance:
- Farmer's Delight Refabricated 3.2.5

Important:
1) Gardez Minecraft 1.21.1.
2) Gardez Cobblemon 1.7.3 / le pack client habituel du serveur.
3) Desactivez les auto-updates.
4) Pour Fabric, utilisez bien la variante Refabricated.

Je reposte ici quand le serveur est de nouveau en ligne.
```

## Template 2 - Serveur en ligne

```text
[SERVEUR EN LIGNE]

La maintenance du lot 7 est terminee, serveur de nouveau disponible.

Mod a avoir cote client pour rejoindre:
- Farmer's Delight Refabricated 3.2.5

Test attendu pendant les prochaines 48h:
- connexion au serveur sans erreur de version
- blocs de cuisine placables et utilisables
- recettes Farmer's Delight visibles et craftables
- signaler tout crash, desync d'inventaire ou souci de recette
```

## Template 3 - Incident / rollback

```text
[INCIDENT MAINTENANCE]

Un probleme est apparu pendant/apres le deploiement du lot 7:
- Farmer's Delight Refabricated 3.2.5

Le serveur passe en rollback vers l'etat precedent pour retablir le service rapidement.

Impact:
- indisponibilite temporaire pendant la restauration
- le lot 7 est suspendu jusqu'a correction

Je confirme ici des que le rollback est termine et que la connexion est stable.
```

## Checklist maintenance

1. poster le Template 1
2. verifier les joueurs connectes
3. executer `./infra/backup.sh`
4. executer `./infra/stop.sh`
5. executer `./infra/mods-install-addon-lot7-farmers-delight.sh`
6. executer `./infra/mods-check-addons-rollout.sh --through-lot 7`
7. executer `./infra/start.sh`
8. verifier l'absence d'erreurs de resolution de mods dans `./data/logs/latest.log`
9. verifier `./infra/status.sh`
10. poster le Template 2 si tout est sain

## Checklist de test

1. client avec `Farmer's Delight Refabricated 3.2.5`: connexion OK
2. recettes visibles et craftables
3. blocs de cuisine placables
4. interactions de base OK
5. absence de spam logs
6. absence de regression gameplay sur la stack deja active

## Rollback rapide

1. `./infra/stop.sh`
2. retirer `FarmersDelight-1.21.1-3.2.5+refabricated.jar`
3. `./infra/start.sh`

Si un vrai retour arriere est requis:

```bash
./infra/restore.sh backups/<backup-file>.tar.gz
```
