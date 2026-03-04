# Runbook: Lot 2 APS Trophies

Objectif:
- preparer la maintenance du lot `2`
- disposer des messages de communication et de la checklist de test

Contexte cible:
- Minecraft `1.21.1`
- Cobblemon `1.7.3`
- lot precedent valide:
  - `Cobblemon Pokenav 2.2.5`

Ajouts du lot:
- serveur:
  - `APS Trophies 1.1.1`
- client obligatoire:
  - `APS Trophies 1.1.1`
- client optionnel recommande:
  - `Catch Indicator 1.4.1`

References:
- rollout principal: `runbooks/addons-rollout-current-world.md`
- pack client: `runbooks/client-pack-addons-rollout.md`
- verrou versions: `audit/addons-compat-lock-20260304.md`
- journal d'execution: `audit/addons-rollout-journal.md`

## Etat de preparation

Preflight deja valide:
- script lot 2 syntaxiquement OK:
  - `./infra/mods-install-addon-lot2-aps-trophies.sh`
- artefact `APS Trophies 1.1.1` telechargeable et hash conforme

Preflight restant avant maintenance:
- verifier qu'aucun joueur n'est connecte
- prendre un backup pre-maintenance
- preparer un joueur test avec `APS Trophies`
- preparer un joueur test sans `Catch Indicator`
- preparer un joueur test avec `Catch Indicator`

## Template 1 - Annonce maintenance

```text
[MAINTENANCE SERVEUR COBBLEMON]

Maintenance prevue aujourd'hui a <HH:MM> (duree estimee: 15 a 20 min).
Objectif: deploiement du lot 2 addons:
- APS Trophies 1.1.1

Ajouts cote client pour rejoindre apres maintenance:
- APS Trophies 1.1.1

Option recommandee, non bloquante:
- Catch Indicator 1.4.1

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

La maintenance du lot 2 est terminee, serveur de nouveau disponible.

Mods a avoir cote client pour rejoindre:
- APS Trophies 1.1.1

Option recommande, non bloquante:
- Catch Indicator 1.4.1

Test attendu pendant les prochaines 24h:
- connexion au serveur sans erreur de version
- attribution d'un trophee de test
- pose / affichage / conservation normale du trophee
- connexion OK avec ou sans Catch Indicator
- signaler tout crash, item invisible, bloc invalide ou desync
```

## Template 3 - Incident / rollback

```text
[INCIDENT MAINTENANCE]

Un probleme est apparu pendant/apres le deploiement du lot 2:
- APS Trophies 1.1.1

Le serveur passe en rollback vers l'etat precedent pour retablir le service rapidement.

Impact:
- indisponibilite temporaire pendant la restauration
- le lot 2 est suspendu jusqu'a correction

Je confirme ici des que le rollback est termine et que la connexion est stable.
```

## Checklist maintenance

1. poster le Template 1
2. verifier les joueurs connectes
3. executer `./infra/backup.sh`
4. executer `./infra/stop.sh`
5. executer `./infra/mods-install-addon-lot2-aps-trophies.sh`
6. executer `./infra/mods-check-addons-rollout.sh --through-lot 2`
7. executer `./infra/start.sh`
8. verifier l'absence d'erreurs de resolution de mods dans `./data/logs/latest.log`
9. verifier `./infra/status.sh`
10. poster le Template 2 si tout est sain

## Checklist de test

1. client avec `APS Trophies 1.1.1`: connexion OK
2. client sans `Catch Indicator`: connexion OK
3. client avec `Catch Indicator 1.4.1`: connexion OK
4. attribution d'un trophee de test
5. pose du trophee
6. affichage correct
7. reprise apres deco/reco

## Rollback rapide

1. `./infra/stop.sh`
2. retirer `aps_trophies-1.21.1-fabric-1.1.1.jar`
3. `./infra/start.sh`

Si un vrai retour arriere est requis:

```bash
./infra/restore.sh backups/<backup-file>.tar.gz
```
