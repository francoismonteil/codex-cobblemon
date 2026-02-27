# Runbook: Storage Rollout (Storage Drawers + Tom's Storage)

## Objectif
Fournir des messages prets a poster pour annoncer:
- la maintenance avant installation
- la remise en ligne du serveur
- un incident avec rollback

Contexte cible:
- Minecraft `1.21.1`
- Modpack: `Cobblemon Official Modpack [Fabric] 1.7.3`
- Mods ajoutes:
  - `Storage Drawers` `1.21.1-13.11.4`
  - `Tom's Simple Storage Mod` `1.21-2.3.0-fabric`

## Template 1 - Annonce maintenance (avant)
```text
[MAINTENANCE SERVEUR COBBLEMON]

Maintenance prevue aujourd'hui a <HH:MM> (duree estimee: 20 a 30 min).
Objectif: ajout des mods de stockage:
- Storage Drawers 1.21.1-13.11.4
- Tom's Simple Storage Mod 1.21-2.3.0-fabric

Important pour les joueurs:
1) Fermez le jeu pendant la maintenance.
2) Apres maintenance, ajoutez exactement ces 2 mods cote client (versions exactes).
3) Gardez le modpack Cobblemon Official [Fabric] 1.7.3 en Minecraft 1.21.1.

Guide detaille:
- runbooks/client-pack-recommended.md

Je reposte ici quand le serveur est de nouveau en ligne.
```

## Template 2 - Serveur en ligne (apres)
```text
[SERVEUR EN LIGNE]

La maintenance est terminee, serveur de nouveau disponible.

Mods a avoir cote client pour rejoindre:
- Storage Drawers 1.21.1-13.11.4
- Tom's Simple Storage Mod 1.21-2.3.0-fabric

Rappel:
- Minecraft 1.21.1
- Cobblemon Official Modpack [Fabric] 1.7.3
- Desactivez les auto-updates pour eviter les version mismatch.

Si vous avez une erreur de version:
1) Verifiez/supprimez la mauvaise version du mod.
2) Reinstallez la version exacte.
3) Relancez le launcher.
```

## Template 3 - Incident / rollback
```text
[INCIDENT MAINTENANCE]

Un probleme de compatibilite est apparu pendant/apres le deploiement des mods de stockage.
Le serveur passe en rollback vers l'etat precedent pour retablir le service rapidement.

Impact:
- indisponibilite temporaire pendant la restauration
- les mods Storage Drawers / Tom's Storage sont suspendus jusqu'a correction

Je confirme ici des que le rollback est termine et que la connexion est stable.
```

## Canal de diffusion recommande
1. Poster le Template 1 dans Discord avant arret du serveur.
2. Apres validation startup/smoke tests, poster le Template 2.
3. En cas d'echec, poster le Template 3.

Option webhook:
- `./infra/friend-info-webhook.sh`
