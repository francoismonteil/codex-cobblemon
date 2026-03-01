# Open World (Village Spawn) – Fabric 1.21.1 + Cobblemon 1.7.3

Objectif: un monde Cobblemon "Pokemon open world" simple, fluide et durable pour **4 joueurs max**, en 24/7, sans map figee.

## Principes (ce que cette procedure garantit)
- Monde ouvert, exploration libre.
- PvP desactive.
- Spawn commun fort mais non intrusif: **un village vanilla** (plaines en priorite).
- Protection du spawn ~150 blocs: **Flan claim** (permet portes/coffres/PNJ, bloque la casse/pose).
- World border initiale: **4000** (rayon 2000), centree sur le spawn.
- Pre-generation complete dans la border: **Chunky** (forme carre, basee sur worldborder).
- Generation "stable": pas de mod worldgen ajoute pour ce setup (juste utilitaires).
- Datapack worldgen applique automatiquement: `acm_pokemon_worldgen` (avant pregen).

## Prerequis
- Acces SSH au serveur Linux.
- Stack Docker Compose fonctionnelle (service `cobblemon`).
- Modpack pinne:
  - `MODRINTH_MODPACK=cobblemon-fabric`
  - `MODRINTH_VERSION=Lydu1ZNo` (Cobblemon Official Modpack [Fabric] **1.7.3**, MC **1.21.1**)
  - Verif rapide:

```bash
grep -E '^MODRINTH_(MODPACK|VERSION)=' .env
```

Si tu viens de modifier localement un script `infra`, un runbook ou un datapack worldgen versionne, synchronise d'abord le serveur depuis le workspace Windows:

```powershell
./infra/deploy-server.ps1 -CreateRemoteBackup -VerifyService
```

Reference: `runbooks/server-sync.md`

## Procedure (nouveau monde)
Toutes les commandes ci-dessous sont a lancer sur le serveur Linux dans `<MC_PROJECT_DIR>`.

1. Initialiser le monde open world (spawn + border + protection + pregen)

Flux standard (ACM uniquement):

```bash
./infra/openworld-village-init.sh
```

Flux ACM + Additional Structures (recommande si tu veux AS sur ce monde):

```bash
./infra/openworld-village-init.sh --with-additionalstructures
```

Flux "retry jusqu'a cluster Pokemart acceptable pres du spawn" (deterministe operationnel):

```bash
./infra/openworld-village-init-until-pokemart.sh --with-additionalstructures --max-attempts 6 --radius 256
```

Ce script:
- fait un backup
- archive `./data/world` vers `./data/world.prev-<timestamp>`
- cree un nouveau monde
- installe `acm_pokemon_worldgen` puis redemarre le serveur
- avec `--with-additionalstructures`: installe `additionalstructures_1211`, force les restarts requis, puis valide ACM+AS avant pregen
- choisit le spawn sur le **village des plaines le plus proche**
- active la border (4000) centree spawn
- cree la protection spawn via Flan (carre 301x301, soit ~150 blocs)
- demarre Chunky (pregen dans la worldborder)
- applique automatiquement le mode "pregen moderee" si `docker-compose.pregen.yml` est present
- **ne place pas** de blocs Pokecenter (healer/PC) au demarrage
- optionnel: via `openworld-village-init-until-pokemart.sh`, reessaie automatiquement la generation jusqu'a obtenir un nombre de clusters Pokemart acceptable proche du spawn (defaut: exactement 1; ou max attempts)

2. Suivre la progression Chunky

```bash
./infra/mc.sh "chunky progress"
docker logs cobblemon --tail 200
```

3. Supervision en arriere-plan (optionnel mais recommande)
Si `MONITOR_WEBHOOK_URL` est configure (Discord), tu peux activer un suivi auto en cron (toutes les 5 min) qui poste des updates (par defaut: toutes les 20%) et la completion:

```bash
./infra/chunky-monitor-enable-cron.sh
tail -f ./logs/chunky-monitor-cron.log
```

Pour arreter:

```bash
./infra/chunky-monitor-disable-cron.sh
```

4. Fin de pre-generation (retour mode normal)
- Quand Chunky annonce la fin (ou quand `chunky progress` indique 100%), tu peux repasser en mode normal:

```bash
docker compose -f docker-compose.yml up -d
```

## "Identite Pokemon" au spawn (manuel, hors demarrage)
L'idee est d'ajouter uniquement les blocs utiles Cobblemon **dans le village existant** (ex: dans une maison), sans construire un batiment complet.
Ces commandes sont **optionnelles** et a lancer uniquement apres le demarrage/openworld init.

### Option A (auto, manuel)
Pose automatiquement un healer + PC **pres du centre du village** (meilleur effort), sans coords manuelles:

```bash
./infra/spawn-village-pokecenter-auto.sh
```

Puis ajoute un petit "habillage" (carpets + utilitaires) autour du kit:

```bash
./infra/spawn-village-pokecenter-decorate.sh
```

Option (si voulu): stocker un petit "welcome cache" (baril) pres du kit (pain, torches, lits, pokeballs):

```bash
./infra/spawn-village-welcome-cache.sh
```

Option (prefab, "vrai batiment"):
Construire un petit Centre Pokemon (empreinte 11x9 ou 9x11 selon orientation) dans un rectangle defini par 4 coins.

```bash
./infra/spawn-pokecenter-prefab.sh --variant decorated \
  <FLx> <FLy> <FLz>  <FRx> <FRy> <FRz>  <BLx> <BLy> <BLz>  <BRx> <BRy> <BRz>
```

Si le script ne trouve pas de place libre (air) a cote du point central, tu peux retenter avec overwrite:

```bash
./infra/spawn-village-pokecenter-auto.sh --force
```

### Option B (manuel, precis)
1. Choisis un point propre dans le village (coordonnees exactes).
2. Pose un healer + PC via script:

```bash
./infra/spawn-poke-kit.sh <x> <y> <z>
```

Option (un peu plus equipe + accent rouge/blanc):

```bash
# Donne les coords du SOL (le bloc sous l'emplacement), le script place a Y+1.
./infra/spawn-village-upgrade.sh <floor_x> <floor_y> <floor_z>
```

Notes:
- Par defaut, `spawn-poke-kit.sh` et `spawn-village-upgrade.sh` **n'ecrasent pas** les blocs si ce n'est pas de l'air. Ajoute `--force` si tu veux overwrite.
- Pour recuperer les coords rapidement, tu peux te mettre sur le bloc cible et lire X/Y/Z via l'ecran F3 (client).

## Extension de la border (plus tard)
1. Choisis une nouvelle taille (ex: 6000 pour rayon 3000).
2. Lance:

```bash
./infra/openworld-border-extend.sh 6000
```

Puis laisse Chunky terminer.

## Notes importantes
- Ne change pas la version du modpack en cours de vie du monde si tu veux garder une generation coherente (worldgen "stable").
- Le PvP est desactive via `./infra/server-profile-openworld-4p.sh` (modifie `./data/server.properties`).
- La protection spawn est geree par Flan (pas `spawn-protection` vanilla).
