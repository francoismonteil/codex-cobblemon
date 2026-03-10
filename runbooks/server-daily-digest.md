# Runbook: Synthese journaliere serveur

Objectif:
- relever chaque jour l'activite serveur et les signaux de stabilite
- suivre une baseline sans changer la configuration
- isoler rapidement si le probleme dominant est le lag, le cycle de vie des entites ou les mouvements joueurs

## Baseline a conserver
- host Linux: `16 Go` RAM
- Minecraft: `MEMORY=6G`
- `Distant Horizons`: `PRE_EXISTING_ONLY`
- `Lithium`: defaut

## Commande recommandee
```bash
py -3 tools/server_log_digest.py --start-date 2026-03-10 --end-date 2026-03-10 --write
```

Sorties:
- `audit/server-log-digest-YYYYMMDD.json`
- `audit/server-log-digest-YYYYMMDD.md`

## Compteurs a suivre
- `cant_keep_up`
- `discarded`
- `moved_too_quickly`
- `moved_wrongly`
- `disconnect_packet_error`
- `join`
- `disconnect`

## Lecture minimale
- `cant_keep_up`:
  - mesure la degradation TPS
  - un faible volume ponctuel est acceptable
  - une rafale continue indique une vraie degradation serveur
- `discarded`:
  - signal principal du probleme Cobblemon actuel
  - suivre les especes dominantes et les heures
- `moved_too_quickly`:
  - signature forte du probleme de monture/vehicule rapide
  - si present avec `Garchomp (vehicle of Sondoku)`, rester prudent sur les montures rapides
- `moved_wrongly`:
  - signature secondaire de desynchronisation joueur/serveur
- `disconnect_packet_error`:
  - bruit reseau secondaire
  - ne pas traiter comme cause racine tant qu'il n'y a pas d'autre preuve

## Regle d'exploitation
- ne pas modifier la heap, les distances ou les mods tant que la baseline n'a pas ete observee plusieurs jours
- si `watchdog > 0`, sortir de la phase d'observation et traiter l'incident
- si `discarded` reste eleve plusieurs jours, preparer ou enrichir un ticket Cobblemon avec preuves exactes

## Reseau de gestion
- IP principale attendue: `192.168.1.19` sur `enp2s0`
- IP de secours: `192.168.1.23` sur `wlp3s0`
- MAC Ethernet pour reservation DHCP: `60:a4:4c:7b:91:fd`
- note:
  - l'IP Ethernet est actuellement attribuee par DHCP
  - garder l'IP Wi-Fi comme fallback tant que la reservation DHCP routeur n'est pas formalisee
