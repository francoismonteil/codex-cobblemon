# Runbook: Lot 5 Raid Dens

Objectif:
- preparer la maintenance du lot `5`
- disposer des messages de communication et de la checklist de test

Contexte cible:
- Minecraft `1.21.1`
- Cobblemon `1.7.3`
- lots precedents valides:
  - `Cobblemon Pokenav 2.2.5`
  - `APS Trophies 1.1.1`
  - `Cobblemon Quick Battle 1.2.5`
  - `Cobbleloots 2.2.2`

Ajouts du lot:
- serveur:
  - `GeckoLib 4.8.4`
  - `Cobblemon Raid Dens 0.8.1+1.21.1`
- client obligatoire:
  - `GeckoLib 4.8.4`
  - `Cobblemon Raid Dens 0.8.1+1.21.1`

Hors perimetre:
- `Raid Dens Design`
  - reste bloque tant qu'une source primaire exacte n'est pas epinglee

References:
- rollout principal: `runbooks/addons-rollout-current-world.md`
- pack client: `runbooks/client-pack-addons-rollout.md`
- verrou versions: `audit/addons-compat-lock-20260304.md`
- journal d'execution: `audit/addons-rollout-journal.md`

## Etat de preparation

Preflight deja valide:
- script lot 5 syntaxiquement OK:
  - `./infra/mods-install-addon-lot5-raiddens.sh`
- artefact `GeckoLib 4.8.4` telechargeable et hash conforme
- artefact `Cobblemon Raid Dens 0.8.1+1.21.1` telechargeable et hash conforme

Preflight restant avant maintenance:
- verifier qu'aucun joueur n'est connecte
- prendre un backup pre-maintenance
- preparer au moins un joueur test avec `GeckoLib` et `Raid Dens`
- preparer une zone de test dans des chunks non critiques

## Template 1 - Annonce maintenance

```text
[MAINTENANCE SERVEUR COBBLEMON]

Maintenance prevue aujourd'hui a <HH:MM> (duree estimee: 20 a 30 min).
Objectif: deploiement du lot 5 addons:
- GeckoLib 4.8.4
- Cobblemon Raid Dens 0.8.1+1.21.1

Ajouts cote client pour rejoindre apres maintenance:
- GeckoLib 4.8.4
- Cobblemon Raid Dens 0.8.1+1.21.1

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

La maintenance du lot 5 est terminee, serveur de nouveau disponible.

Mods a avoir cote client pour rejoindre:
- GeckoLib 4.8.4
- Cobblemon Raid Dens 0.8.1+1.21.1

Test attendu pendant les prochains jours:
- connexion au serveur sans erreur de version
- apparition de dens dans de nouveaux chunks
- entree/sortie de raid fonctionnelle
- recompenses coherentes
- signaler tout crash, chunk corrompu, raid bloque ou comportement anormal
```

## Template 3 - Incident / rollback

```text
[INCIDENT MAINTENANCE]

Un probleme est apparu pendant/apres le deploiement du lot 5:
- GeckoLib 4.8.4
- Cobblemon Raid Dens 0.8.1+1.21.1

Le serveur passe en rollback vers l'etat precedent pour retablir le service rapidement.

Impact:
- indisponibilite temporaire pendant la restauration
- le lot 5 est suspendu jusqu'a correction

Je confirme ici des que le rollback est termine et que la connexion est stable.
```

## Checklist maintenance

1. poster le Template 1
2. verifier les joueurs connectes
3. executer `./infra/backup.sh`
4. executer `./infra/stop.sh`
5. executer `./infra/mods-install-addon-lot5-raiddens.sh`
6. executer `./infra/mods-check-addons-rollout.sh --through-lot 5`
7. executer `./infra/start.sh`
8. verifier l'absence d'erreurs de resolution de mods dans `./data/logs/latest.log`
9. verifier `./infra/status.sh`
10. poster le Template 2 si tout est sain

## Checklist de test

1. client avec `GeckoLib 4.8.4` et `Raid Dens 0.8.1+1.21.1`: connexion OK
2. apparition de dens dans de nouveaux chunks
3. entree dans un raid
4. sortie de raid
5. recompenses coherentes
6. absence de corruption de chunk
7. absence de spam logs lie a generation / entites

## Rollback rapide

1. `./infra/stop.sh`
2. retirer `geckolib-fabric-1.21.1-4.8.4.jar`
3. retirer `cobblemonraiddens-fabric-0.8.1+1.21.1.jar`
4. `./infra/start.sh`

Si les dens ont deja ete generees et jouees, preferer un vrai retour arriere:

```bash
./infra/restore.sh backups/<backup-file>.tar.gz
```
