# Runbook: DDNS (DuckDNS)

## Objectif
Obtenir une adresse stable pour tes amis (meme si l'IP publique change).

## 1) Creer un sous-domaine DuckDNS
1. Aller sur DuckDNS et creer un domaine (ex: `monserveur-duckdns`).
2. Recuperer le `token`.

## 2) Configurer le serveur
Sur la machine `<MC_SSH_USER>@<MC_SERVER_HOST>`, dans `<MC_PROJECT_DIR>`:

1. Renseigner `.env`:
   - `DUCKDNS_DOMAINS=monserveur-duckdns`
   - `DUCKDNS_TOKEN=...`
2. Executer un test:
   - `./infra/ddns-duckdns.sh`
3. Ajouter un cron (toutes les 5 minutes):
   - `*/5 * * * * cd <MC_PROJECT_DIR> && <MC_PROJECT_DIR>/infra/ddns-duckdns.sh >> <MC_PROJECT_DIR>/logs/ddns-duckdns-cron.log 2>&1 # minecraft-ddns-duckdns`

## 3) Adresse a donner aux amis
- `monserveur-duckdns.duckdns.org:25565`

## Notes
- La whitelist est active: il faudra ajouter les pseudos/UUID des amis pour qu'ils puissent entrer.
- Si tu utilises un autre fournisseur (No-IP, Cloudflare), on fera un runbook/script specifique.
