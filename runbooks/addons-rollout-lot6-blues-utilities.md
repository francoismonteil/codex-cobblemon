# Runbook: Lot 6 Blue's Cobblemon Utilities

Objectif:
- preparer la maintenance du lot `6`
- disposer des messages de communication et de la checklist de test

Contexte cible:
- Minecraft `1.21.1`
- Cobblemon `1.7.3`
- lots precedents valides:
  - `Cobblemon Pokenav 2.2.5`
  - `APS Trophies 1.1.1`
  - `Cobblemon Quick Battle 1.2.5`
  - `Cobbleloots 2.2.2`
- lot actuellement en observation:
  - `GeckoLib 4.8.4`
  - `Cobblemon Raid Dens 0.8.1+1.21.1`

Ajouts du lot:
- serveur:
  - `Blue's Cobblemon Utilities 4.0.0`
  - forme de livraison:
    - datapack zip dans `./data/world/datapacks`

Ajouts client:
- aucun jar obligatoire dans ce rollout

Point d'attention:
- le retrait infra est simple
- mais les changements deja appliques aux Pokemon ne sont pas attendus comme automatiquement reversibles

References:
- rollout principal: `runbooks/addons-rollout-current-world.md`
- pack client: `runbooks/client-pack-addons-rollout.md`
- verrou versions: `audit/addons-compat-lock-20260304.md`
- journal d'execution: `audit/addons-rollout-journal.md`

## Etat de preparation

Preflight deja valide:
- script lot 6 syntaxiquement OK:
  - `./infra/mods-install-addon-lot6-blues-utilities.sh`
- archive `Blue's Cobblemon Utilities 4.0.0` telechargeable et hash conforme
- chemins verifies sur l'hote:
  - `./data/world`
  - `./data/world/datapacks`

Preflight restant avant maintenance:
- verifier qu'aucun joueur n'est connecte
- prendre un backup pre-maintenance
- preparer un test ferme `admins + 1 joueur volontaire`

## Template 1 - Annonce maintenance

```text
[MAINTENANCE SERVEUR COBBLEMON]

Maintenance prevue aujourd'hui a <HH:MM> (duree estimee: 15 a 20 min).
Objectif: deploiement du lot 6 addons:
- Blue's Cobblemon Utilities 4.0.0

Important:
- aucun mod client supplementaire n'est requis pour ce lot
- le test initial sera volontairement restreint

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

La maintenance du lot 6 est terminee, serveur de nouveau disponible.

Rappel:
- aucun mod client supplementaire n'est requis pour ce lot

Phase de test:
- lot ouvert en perimetre restreint au demarrage
- merci de ne pas utiliser les fonctions du lot 6 hors cadre valide

Test attendu:
- datapack actif sans erreur
- fonctions autorisees utilisables
- pas de crash ni erreur apres reload / reboot
- signaler tout effet inattendu sur les Pokemon ou les items
```

## Template 3 - Incident / rollback

```text
[INCIDENT MAINTENANCE]

Un probleme est apparu pendant/apres le deploiement du lot 6:
- Blue's Cobblemon Utilities 4.0.0

Le serveur passe en rollback vers l'etat precedent pour retablir le service rapidement.

Impact:
- indisponibilite temporaire pendant la restauration
- le lot 6 est suspendu jusqu'a correction

Je confirme ici des que le rollback est termine et que la connexion est stable.
```

## Checklist maintenance

1. poster le Template 1
2. verifier les joueurs connectes
3. executer `./infra/backup.sh`
4. executer `./infra/stop.sh`
5. executer `./infra/mods-install-addon-lot6-blues-utilities.sh`
6. executer `./infra/mods-check-addons-rollout.sh --through-lot 6`
7. executer `./infra/start.sh`
8. verifier l'absence d'erreurs datapack dans `./data/logs/latest.log`
9. verifier `./infra/status.sh`
10. poster le Template 2 si tout est sain

## Checklist de test

1. `./infra/mc.sh "datapack list enabled"` contient `file/blues-cobblemon-utilities-4.0.0.zip`
2. test en perimetre restreint `admins + 1 joueur volontaire`
3. verification des fonctions explicitement autorisees
4. verification qu'une desactivation coupe bien les usages futurs si besoin
5. absence d'erreur apres `reload`
6. absence d'erreur apres reboot

## Rollback rapide

1. `./infra/stop.sh`
2. retirer `./data/world/datapacks/blues-cobblemon-utilities-4.0.0.zip`
3. `./infra/start.sh`

Si un vrai retour arriere gameplay est requis:

```bash
./infra/restore.sh backups/<backup-file>.tar.gz
```
