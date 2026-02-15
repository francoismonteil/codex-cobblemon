# Progression (Badges)

Objectif: avoir une progression "casual mais motivante" sans ajouter de plugins/mods serveur.

## Principe
- Un badge = un scoreboard `dummy` (0/1).
- Le total est calcule dans `badge_total`.
- Attribution: commande admin via console (script `infra/badge.sh`).

Badges disponibles (style Kanto, renommables ensuite):
- boulder, cascade, thunder, rainbow, soul, marsh, volcano, earth

## Initialisation
Sur le serveur:
```bash
cd /home/linux/codex-cobblemon
./infra/progression-init.sh
```

## Donner un badge
```bash
./infra/badge.sh grant <Pseudo> <badge>
```

Exemple:
```bash
./infra/badge.sh grant <player> boulder
```

## Voir le statut d'un joueur
```bash
./infra/badge.sh status <Pseudo>
```

## Note
Pour automatiser (quand on voudra):
- ajouter des command blocks dans l'arene (ou des PNJ/mod) pour verifier les scores et ouvrir/fermer des acces.
- ou passer a un mod/plugin de "quests" / "ranks" si on veut du 100% automatisme.
