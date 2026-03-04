# Runbook: Lot 4 Cobbleloots

Objectif:
- preparer la maintenance du lot `4`
- disposer des messages de communication et de la checklist de test

Contexte cible:
- Minecraft `1.21.1`
- Cobblemon `1.7.3`
- lots precedents valides:
  - `Cobblemon Pokenav 2.2.5`
  - `APS Trophies 1.1.1`
  - `Cobblemon Quick Battle 1.2.5`

Ajouts du lot:
- serveur:
  - `Cobbleloots 2.2.2`
- client obligatoire:
  - `Cobbleloots 2.2.2`

References:
- rollout principal: `runbooks/addons-rollout-current-world.md`
- pack client: `runbooks/client-pack-addons-rollout.md`
- verrou versions: `audit/addons-compat-lock-20260304.md`
- journal d'execution: `audit/addons-rollout-journal.md`

## Etat de preparation

Preflight deja valide:
- script lot 4 syntaxiquement OK:
  - `./infra/mods-install-addon-lot4-cobbleloots.sh`
- artefact `Cobbleloots 2.2.2` telechargeable et hash conforme

Preflight restant avant maintenance:
- verifier qu'aucun joueur n'est connecte
- prendre un backup pre-maintenance
- preparer au moins un joueur test avec `Cobbleloots 2.2.2`
- prevoir une zone de nouveaux chunks pour observer la generation de loot

## Template 1 - Annonce maintenance

```text
[MAINTENANCE SERVEUR COBBLEMON]

Maintenance prevue aujourd'hui a <HH:MM> (duree estimee: 15 a 20 min).
Objectif: deploiement du lot 4 addons:
- Cobbleloots 2.2.2

Ajout cote client pour rejoindre apres maintenance:
- Cobbleloots 2.2.2

Rappels:
1) Gardez Minecraft 1.21.1.
2) Gardez Cobblemon 1.7.3 / le pack client habituel du serveur.
3) Desactivez les auto-updates.
4) N'ajoutez pas les lots suivants, ils ne sont pas deployes.

Je reposte ici quand le serveur est de nouveau en ligne.
```

## Template 2 - Serveur en ligne

```text
[SERVEUR EN LIGNE]

La maintenance du lot 4 est terminee, serveur de nouveau disponible.

Mod a avoir cote client pour rejoindre:
- Cobbleloots 2.2.2

Test attendu pendant les prochaines 72h:
- connexion au serveur sans erreur de version
- generation de loot dans de nouveaux chunks
- recompenses coherentes
- pas de regression sur le loot vanilla ou Cobblemon existant
- signaler tout loot bugge, table de loot cassée, erreur ou comportement anormal
```

## Template 3 - Incident / rollback

```text
[INCIDENT MAINTENANCE]

Un probleme est apparu pendant/apres le deploiement du lot 4:
- Cobbleloots 2.2.2

Le serveur passe en rollback vers l'etat precedent pour retablir le service rapidement.

Impact:
- indisponibilite temporaire pendant la restauration
- le lot 4 est suspendu jusqu'a correction

Je confirme ici des que le rollback est termine et que la connexion est stable.
```

## Checklist maintenance

1. poster le Template 1
2. verifier les joueurs connectes
3. executer `./infra/backup.sh`
4. executer `./infra/stop.sh`
5. executer `./infra/mods-install-addon-lot4-cobbleloots.sh`
6. executer `./infra/mods-check-addons-rollout.sh --through-lot 4`
7. executer `./infra/start.sh`
8. verifier l'absence d'erreurs de resolution de mods dans `./data/logs/latest.log`
9. verifier `./infra/status.sh`
10. poster le Template 2 si tout est sain

## Checklist de test

1. client avec `Cobbleloots 2.2.2`: connexion OK
2. generation de loot dans de nouveaux chunks
3. recompenses coherentes
4. absence d'erreurs repetees dans les logs
5. pas de regression du loot vanilla
6. pas de regression du loot Cobblemon existant

## Rollback rapide

1. `./infra/stop.sh`
2. retirer `cobbleloots-fabric-2.2.2.jar`
3. `./infra/start.sh`

Si un vrai retour arriere est requis:

```bash
./infra/restore.sh backups/<backup-file>.tar.gz
```
