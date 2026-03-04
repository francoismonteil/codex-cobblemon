# Runbook: Lot 8 Botany Pots

Objectif:
- preparer la maintenance du lot `8`
- disposer des messages de communication et de la checklist de test

Contexte cible:
- Minecraft `1.21.1`
- Cobblemon `1.7.3`
- lot `7` valide avant ouverture

Ajouts du lot:
- serveur:
  - `Architectury API 13.0.8+fabric`
  - `Bookshelf 21.1.81`
  - `Prickle 21.1.11`
  - `Botany Pots 21.1.41`
  - `Cobblemon Botany Pots 1.0.1`
- client obligatoire:
  - `Architectury API 13.0.8+fabric`
  - `Bookshelf 21.1.81`
  - `Prickle 21.1.11`
  - `Botany Pots 21.1.41`
  - `Cobblemon Botany Pots 1.0.1`

References:
- rollout principal: `runbooks/addons-rollout-current-world.md`
- pack client: `runbooks/client-pack-addons-rollout.md`
- verrou versions: `audit/addons-compat-lock-20260304.md`
- journal d'execution: `audit/addons-rollout-journal.md`

## Etat de preparation

Preflight deja valide:
- script lot 8 syntaxiquement OK:
  - `./infra/mods-install-addon-lot8-botany-pots.sh`
- les quatre artefacts sont telechargeables et hashes conformes
- la dependance `Architectury API 13.0.8+fabric` est incluse

Preflight restant avant maintenance:
- verifier qu'aucun joueur n'est connecte
- prendre un backup pre-maintenance
- preparer au moins un joueur test avec la pile client complete

## Template 1 - Annonce maintenance

```text
[MAINTENANCE SERVEUR COBBLEMON]

Maintenance prevue aujourd'hui a <HH:MM> (duree estimee: 15 a 25 min).
Objectif: deploiement du lot 8 addons:
- Architectury API 13.0.8+fabric
- Bookshelf 21.1.81
- Prickle 21.1.11
- Botany Pots 21.1.41
- Cobblemon Botany Pots 1.0.1

Ajouts cote client pour rejoindre apres maintenance:
- Architectury API 13.0.8+fabric
- Bookshelf 21.1.81
- Prickle 21.1.11
- Botany Pots 21.1.41
- Cobblemon Botany Pots 1.0.1

Rappels:
1) Gardez Minecraft 1.21.1.
2) Gardez Cobblemon 1.7.3 / le pack client habituel du serveur.
3) Desactivez les auto-updates.
4) N'ajoutez pas d'autres integrations Farmer's Delight non annoncees.

Je reposte ici quand le serveur est de nouveau en ligne.
```

## Template 2 - Serveur en ligne

```text
[SERVEUR EN LIGNE]

La maintenance du lot 8 est terminee, serveur de nouveau disponible.

Pile client obligatoire pour rejoindre:
- Architectury API 13.0.8+fabric
- Bookshelf 21.1.81
- Prickle 21.1.11
- Botany Pots 21.1.41
- Cobblemon Botany Pots 1.0.1

Test attendu pendant les prochaines 72h:
- connexion au serveur sans erreur de version
- pot placable et fonctionnel
- culture Cobblemon dans les pots OK
- automation simple OK
- signaler tout crash, duplication ou comportement anormal
```

## Template 3 - Incident / rollback

```text
[INCIDENT MAINTENANCE]

Un probleme est apparu pendant/apres le deploiement du lot 8:
- Architectury API 13.0.8+fabric
- Bookshelf 21.1.81
- Prickle 21.1.11
- Botany Pots 21.1.41
- Cobblemon Botany Pots 1.0.1

Le serveur passe en rollback vers l'etat precedent pour retablir le service rapidement.

Impact:
- indisponibilite temporaire pendant la restauration
- le lot 8 est suspendu jusqu'a correction

Je confirme ici des que le rollback est termine et que la connexion est stable.
```

## Checklist maintenance

1. poster le Template 1
2. verifier les joueurs connectes
3. executer `./infra/backup.sh`
4. executer `./infra/stop.sh`
5. executer `./infra/mods-install-addon-lot8-botany-pots.sh`
6. executer `./infra/mods-check-addons-rollout.sh --through-lot 8`
7. executer `./infra/start.sh`
8. verifier l'absence d'erreurs de resolution de mods dans `./data/logs/latest.log`
9. verifier `./infra/status.sh`
10. poster le Template 2 si tout est sain

## Checklist de test

1. client avec la pile complete: connexion OK
2. pot placable
3. support des cultures Cobblemon confirme
4. recolte OK
5. hopper / stockage simple OK
6. absence de duplication
7. absence de spam logs ou crash

## Rollback rapide

1. `./infra/stop.sh`
2. retirer:
   - `architectury-13.0.8-fabric.jar`
   - `bookshelf-fabric-1.21.1-21.1.81.jar`
   - `prickle-fabric-1.21.1-21.1.11.jar`
   - `botanypots-fabric-1.21.1-21.1.41.jar`
   - `cobblemon_pots-fabric-1.0.1.jar`
3. `./infra/start.sh`

Si un vrai retour arriere est requis:

```bash
./infra/restore.sh backups/<backup-file>.tar.gz
```
