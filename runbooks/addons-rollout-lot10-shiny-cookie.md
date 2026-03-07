# Runbook: Lot 10 Shiny Cookie

Objectif:
- preparer la maintenance du lot `10`
- disposer des messages de communication et de la checklist de test

Contexte cible:
- Minecraft `1.21.1`
- Cobblemon `1.7.3`
- lots `1` a `9` actifs

Ajouts du lot:
- serveur:
  - `Cobblemon: Shiny Cookie 0.0.1`
- client obligatoire:
  - `Cobblemon: Shiny Cookie 0.0.1`

Position retenue:
- la persistance gameplay est explicitement acceptee pour ce lot
- un retrait du jar n'annule pas les effets deja appliques aux Pokemon

References:
- rollout principal: `runbooks/addons-rollout-current-world.md`
- pack client: `runbooks/client-pack-addons-rollout.md`
- verrou versions: `audit/addons-compat-lock-20260304.md`
- journal d'execution: `audit/addons-rollout-journal.md`

## Etat de preparation

Preflight deja valide:
- script lot 10 syntaxiquement OK:
  - `./infra/mods-install-addon-lot10-shiny-cookie.sh`
- artefact `Cobblemon: Shiny Cookie 0.0.1` telechargeable et hash conforme

Preflight restant avant maintenance:
- verifier qu'aucun joueur n'est connecte
- prendre un backup pre-maintenance
- preparer au moins un joueur test avec `Cobblemon: Shiny Cookie 0.0.1`

## Template 1 - Annonce maintenance

```text
[MAINTENANCE SERVEUR COBBLEMON]

Maintenance prevue aujourd'hui a <HH:MM> (duree estimee: 15 a 20 min).
Objectif: deploiement du lot 10 addons:
- Cobblemon: Shiny Cookie 0.0.1

Ajout cote client pour rejoindre apres maintenance:
- Cobblemon: Shiny Cookie 0.0.1

Important:
1) Gardez Minecraft 1.21.1.
2) Gardez Cobblemon 1.7.3 / le pack client habituel du serveur.
3) Desactivez les auto-updates.
4) La persistance gameplay de ce lot est assumee.

Je reposte ici quand le serveur est de nouveau en ligne.
```

## Template 2 - Serveur en ligne

```text
[SERVEUR EN LIGNE]

La maintenance du lot 10 est terminee, serveur de nouveau disponible.

Mod a avoir cote client pour rejoindre:
- Cobblemon: Shiny Cookie 0.0.1

Test attendu pendant les prochaines 48h:
- connexion au serveur sans erreur de version
- obtention / utilisation controlee OK
- signaler tout comportement anormal, consommation sans effet ou crash
```

## Template 3 - Incident / rollback

```text
[INCIDENT MAINTENANCE]

Un probleme est apparu pendant/apres le deploiement du lot 10:
- Cobblemon: Shiny Cookie 0.0.1

Le serveur passe en rollback vers l'etat precedent pour retablir le service rapidement.

Impact:
- indisponibilite temporaire pendant la restauration
- le lot 10 est suspendu jusqu'a correction

Je confirme ici des que le rollback est termine et que la connexion est stable.
```

## Checklist maintenance

1. poster le Template 1
2. verifier les joueurs connectes
3. executer `./infra/backup.sh`
4. executer `./infra/stop.sh`
5. executer `./infra/mods-install-addon-lot10-shiny-cookie.sh`
6. executer `./infra/mods-check-addons-rollout.sh --through-lot 10`
7. executer `./infra/start.sh`
8. verifier l'absence d'erreurs de resolution de mods dans `./data/logs/latest.log`
9. verifier `./infra/status.sh`
10. poster le Template 2 si tout est sain

## Checklist de test

1. client avec `Cobblemon: Shiny Cookie 0.0.1`: connexion OK
2. obtention controlee
3. utilisation controlee
4. absence de crash
5. absence d'effet anormal hors perimetre attendu

## Rollback rapide

1. `./infra/stop.sh`
2. retirer `shinycookie-fabric-0.0.1.jar`
3. `./infra/start.sh`

Si un vrai retour arriere integral est requis:

```bash
./infra/restore.sh backups/<backup-file>.tar.gz
```
