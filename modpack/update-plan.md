Plan de mise à jour / déploiement pour serveur Cobblemon (modpack officiel - Lydu1ZNo)

Préconditions

- Backup obligatoire:
  - Sauvegarder le répertoire `world/` complet (all dimensions) vers `backups/world-YYYYMMDD-HHMMSS.zip`.
  - Sauvegarder le répertoire `server/` (server.properties, ops.json, whitelist.json, eula.txt, scripts) vers `backups/server-config-YYYYMMDD-HHMMSS.zip`.
  - Sauvegarder le dossier `mods/` actuel et `config/` vers `backups/mods-config-YYYYMMDD-HHMMSS.zip`.
  - Vérifier intégrité des backups (taille non nulle, capacité d'extraction rapide).
- Downtime prévu: le serveur sera arrêté pendant l'opération (prévoir 10-30 minutes selon la taille du modpack et la vitesse du réseau/disque).
- Permissions: l'utilisateur effectuant l'opération doit avoir accès aux fichiers du serveur et aux volumes Docker (si containerisé).

Étapes (déploiement initial ou update en place)

1. Planification & communication
   - Annoncer la fenêtre de maintenance aux joueurs.
   - Vérifier que les sauvegardes automatiques sont désactivées durant l'opération pour éviter conflits.

2. Rassembler les artefacts
   - Télécharger la version du modpack via Modrinth: https://modrinth.com/modpack/cobblemon-fabric/version/Lydu1ZNo.
   - Extraire (ou récupérer via l'API) le manifest de la version et pinner chaque mod/fichier.
   - Placer tous les fichiers .jar requis dans `deploy/artifacts/`.

3. Stop production
   - Arrêter le serveur Minecraft / conteneur Docker proprement:
     - Si service systemd / script: `# stop server`
     - Si Docker: `docker stop <container>`

4. Remplacer les mods / loader
   - Sauvegarder l'ancien dossier `mods/` (déjà fait).
   - Copier `deploy/artifacts/*.jar` dans le dossier `server/mods/`.
   - Mettre à jour `server/jars/` ou l'image Docker pour utiliser Fabric Loader et la version Java voulue.

5. Configurer Java & Fabric
   - S'assurer que l'image Docker ou l'hôte utilise Java 17 (ou la version vérifiée).
   - S'assurer que Fabric Loader et Fabric API versions pined sont présents (vérifier `fabric-server-launch.jar` ou l'équivalent du modpack).

6. Lancer en mode validation
   - Démarrer le serveur en mode console (pas en background) et observer le démarrage:
     - Valider que la version de Minecraft affichée est 1.21.1.
     - Valider que Fabric Loader et Fabric API se chargent sans erreurs.
     - Surveiller les erreurs dans la console (mod startup failures, NoClassDefFoundError, Incompatible mods).

7. Validation fonctionnelle
   - Se connecter localement au serveur (client compatible) et vérifier:
     - Le monde charge correctement.
     - Les entités/monstres du mod Cobblemon apparaissent et les commandes de base répondent.
     - Les plugins/commandes d'administration fonctionnent (ops, whitelist).
   - Vérifier les logs (server latest.log / debug.log) pour exceptions critiques.

8. Mise en production
   - Si tout est OK, redémarrer le serveur en mode production / planifié.
   - Informer les joueurs de la disponibilité.

Rollback steps

- Si un problème critique est détecté durant la validation ou dans les heures suivant la mise en production:
  1. Stopper le serveur immédiatement.
  2. Restaurer les fichiers depuis les backups:
     - Extraire `backups/server-config-YYYYMMDD-HHMMSS.zip` vers le répertoire serveur.
     - Extraire `backups/mods-config-YYYYMMDD-HHMMSS.zip` vers `server/mods/` et `server/config/`.
     - Restaurer le monde: extraire `backups/world-YYYYMMDD-HHMMSS.zip` dans `world/` (remplacez). 
  3. Démarrer le serveur précédent (avec l'image Docker/Java antérieur si utilisé).
  4. Vérifier logs et confirmer que le serveur fonctionne comme avant.
  5. Communiquer la rollback aux utilisateurs et planifier une nouvelle fenêtre de maintenance pour corriger le problème.

Validation checklist (quick)

- [ ] Backups créés et testés
- [ ] Artefacts du modpack (Lydu1ZNo) téléchargés et checksums pined
- [ ] Java runtime verifié (17 ou autre confirmé)
- [ ] Fabric Loader & API pined et présents
- [ ] Démarrage server OK (logs sans erreurs critiques)
- [ ] Connexion client OK et tests de gameplay basiques passés

Notes Docker spécifiques

- Image Docker recommandée: builder basée sur `openjdk:17-jdk` (ou distribution adoptopenjdk/temurin 17) pour correspondre à Java 17.
- Volume mapping recommandés:
  - -v /path/to/server:/data
  - -v /path/to/backups:/backups
- Entrypoint: démarrer via `java -Xms1G -Xmx4G -jar fabric-server-launch.jar nogui` (ajuster mémoire selon besoin).

Fin du plan.
