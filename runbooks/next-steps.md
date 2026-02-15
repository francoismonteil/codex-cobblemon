# Next Steps (roadmap)

Last updated: 2026-02-12

## 1) Onboarding amis (whitelist / op)
- Objectif: ajouter rapidement un joueur quand il te donne son pseudo.
- Outils:
  - `infra/mc.sh` (commande console)
  - `infra/player.sh` (helper whitelist/op)

## 2) Alerting Discord
- Renseigner `MONITOR_WEBHOOK_URL` dans `.env` pour recevoir les alertes du script `infra/monitor.sh`.

## 3) Backups offsite
- Copier regulierement `./backups/backup-*.tar.gz` vers un autre support (NAS/cloud).

## 4) Politique de restart
- Garder le restart quotidien si tu veux, mais alerter si echec.
- Option: restart conditionnel (health/ressources) au lieu d'un restart fixe.

## 5) Exposition Internet minimale
- Garder seulement `25565/tcp` expose.
- SSH: eviter l'exposition WAN, ou limiter l'acces au strict necessaire.

## 6) Spawn "ville Pokemon" (moderne)
- Runbook: `runbooks/spawn-city.md`
- Decisions:
  - shop = emeralds
  - gym = decor + arene

## 7) Progression (badges / objectifs)
- Runbook: `runbooks/progression.md`
- Objectif: une progression simple et lisible (badges) sans rajouter de plugins.
