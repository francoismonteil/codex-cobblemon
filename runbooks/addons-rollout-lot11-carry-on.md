# Runbook: Lot 11 Carry On

Objectif:
- preparer la maintenance du lot `11`
- disposer des messages de communication et de la checklist de test

Contexte cible:
- Minecraft `1.21.1`
- Cobblemon `1.7.3`
- lots `1` a `10` actifs

Ajouts du lot:
- serveur:
  - `Carry On 2.2.4.4`
- client obligatoire:
  - `Carry On 2.2.4.4`

References:
- rollout principal: `runbooks/addons-rollout-current-world.md`
- pack client: `runbooks/client-pack-addons-rollout.md`
- verrou versions: `audit/addons-compat-lock-20260304.md`
- journal d'execution: `audit/addons-rollout-journal.md`

## Etat de preparation

Preflight deja valide:
- script lot 11 syntaxiquement OK:
  - `./infra/mods-install-addon-lot11-carry-on.sh`
- artefact `Carry On 2.2.4.4` telechargeable et hash conforme

Preflight restant avant maintenance:
- verifier qu'aucun joueur n'est connecte
- prendre un backup pre-maintenance
- preparer au moins un joueur test avec `Carry On 2.2.4.4`

## Template 1 - Annonce maintenance

```text
[MAINTENANCE SERVEUR COBBLEMON]

Maintenance prevue aujourd'hui a <HH:MM> (duree estimee: 15 a 20 min).
Objectif: deploiement du lot 11 addons:
- Carry On 2.2.4.4

Ajout cote client pour rejoindre apres maintenance:
- Carry On 2.2.4.4

Important:
1) Gardez Minecraft 1.21.1.
2) Gardez Cobblemon 1.7.3 / le pack client habituel du serveur.
3) Desactivez les auto-updates.

Je reposte ici quand le serveur est de nouveau en ligne.
```

## Template 2 - Serveur en ligne

```text
[SERVEUR EN LIGNE]

La maintenance du lot 11 est terminee, serveur de nouveau disponible.

Mod a avoir cote client pour rejoindre:
- Carry On 2.2.4.4

Test attendu pendant les prochaines 48h:
- connexion au serveur sans erreur de version
- prise/portage d'entites et de blocs conforme
- pas de duplication ni crash
```

## Template 3 - Incident / rollback

```text
[INCIDENT MAINTENANCE]

Un probleme est apparu pendant/apres le deploiement du lot 11:
- Carry On 2.2.4.4

Le serveur passe en rollback vers l'etat precedent pour retablir le service rapidement.

Impact:
- indisponibilite temporaire pendant la restauration
- le lot 11 est suspendu jusqu'a correction

Je confirme ici des que le rollback est termine et que la connexion est stable.
```

## Checklist maintenance

1. poster le Template 1
2. verifier les joueurs connectes
3. executer `./infra/backup.sh`
4. executer `./infra/stop.sh`
5. executer `./infra/mods-install-addon-lot11-carry-on.sh`
6. executer `./infra/mods-check-addons-rollout.sh --through-lot 11`
7. executer `./infra/start.sh`
8. verifier l'absence d'erreurs de resolution de mods dans `./data/logs/latest.log`
9. verifier `./infra/status.sh`
10. poster le Template 2 si tout est sain

## Checklist de test

1. client avec `Carry On 2.2.4.4`: connexion OK
2. prise/portage d'un bloc vanilla simple: OK
3. prise/portage d'une entite vanilla simple: OK
4. test de pose/relache sans duplication
5. absence de crash

## Rollback rapide

1. `./infra/stop.sh`
2. retirer `carryon-fabric-1.21.1-2.2.4.4.jar`
3. `./infra/start.sh`

Si un vrai retour arriere integral est requis:

```bash
./infra/restore.sh backups/<backup-file>.tar.gz
```
