# Synthese journaliere serveur

- Fenetre: `2026-03-10` a `2026-03-10`
- Genere le: `2026-03-10T17:36:33.819526+00:00`

## Etat courant

- Statut conteneur: `running`
- Sante conteneur: `healthy`
- Players online au relevé: `0`
- CPU conteneur: `21.25%`
- Memoire conteneur: `7.155GiB / 15.5GiB`

## Compteurs

- `join`: `4`
- `disconnect`: `4`
- `cant_keep_up`: `2`
- `discarded`: `54`
- `moved_too_quickly`: `0`
- `moved_wrongly`: `3`
- `disconnect_packet_error`: `142`
- `watchdog`: `0`
- `server_stop`: `1`
- `server_done`: `1`

## Activite joueurs

- `Totamote`: 2026-03-10 13:40:18 join | 2026-03-10 15:31:30 disconnect | 2026-03-10 15:37:15 join | 2026-03-10 17:44:22 disconnect
- `TiidyMan`: 2026-03-10 15:05:33 join | 2026-03-10 15:15:50 disconnect | 2026-03-10 15:16:25 join | 2026-03-10 16:36:15 disconnect

## DISCARDED

- `Volcarona`: `23`
- `Munchlax`: `17`
- `Blaziken`: `7`
- `Aerodactyl`: `3`
- `Archeops`: `1`
- `Greninja`: `1`
- `Phantump`: `1`
- `Gengar`: `1`

## Repartition horaire

- `discarded_by_hour`:
  - `2026-03-10 13`: `5`
  - `2026-03-10 14`: `2`
  - `2026-03-10 15`: `26`
  - `2026-03-10 16`: `15`
  - `2026-03-10 17`: `6`
- `lag_by_hour`:
  - `2026-03-10 11`: `1`
  - `2026-03-10 17`: `1`

## Signaux recents

- `2026-03-10 16:58:22` `discarded` `Volcarona`: Entity PokemonEntity['Volcarona'/35582, l='ServerLevel[world]', x=-1559.86, y=63.00, z=2674.73, removed=DISCARDED] wasn't found in section class_4076{x=-98, y=3, z=167} (destroying due to DISCARDED)
- `2026-03-10 16:59:16` `discarded` `Volcarona`: Entity PokemonEntity['Volcarona'/36143, l='ServerLevel[world]', x=-1225.32, y=80.00, z=2849.72, removed=DISCARDED] wasn't found in section class_4076{x=-77, y=5, z=178} (destroying due to DISCARDED)
- `2026-03-10 17:00:13` `discarded` `Volcarona`: Entity PokemonEntity['Volcarona'/37006, l='ServerLevel[world]', x=-1189.67, y=92.00, z=2839.93, removed=DISCARDED] wasn't found in section class_4076{x=-75, y=5, z=177} (destroying due to DISCARDED)
- `2026-03-10 17:03:24` `discarded` `Blaziken`: Entity PokemonEntity['Blaziken'/37197, l='ServerLevel[world]', x=-1120.89, y=64.00, z=2736.91, removed=DISCARDED] wasn't found in section class_4076{x=-71, y=4, z=171} (destroying due to DISCARDED)
- `2026-03-10 17:05:05` `discarded` `Gengar`: Entity PokemonEntity['Gengar'/37682, l='ServerLevel[world]', x=-1155.26, y=67.00, z=2711.73, removed=DISCARDED] wasn't found in section class_4076{x=-73, y=4, z=169} (destroying due to DISCARDED)
- `2026-03-10 17:07:10` `disconnect_packet_error` ``: Error sending packet clientbound/minecraft:disconnect
- `2026-03-10 17:07:35` `discarded` `Volcarona`: Entity PokemonEntity['Volcarona'/38493, l='ServerLevel[world]', x=-1112.00, y=77.00, z=2810.57, removed=DISCARDED] wasn't found in section class_4076{x=-70, y=4, z=175} (destroying due to DISCARDED)
- `2026-03-10 17:08:05` `moved_wrongly` `Totamote`: Totamote moved wrongly!
- `2026-03-10 17:08:08` `discarded` `Volcarona`: Entity PokemonEntity['Volcarona'/38502, l='ServerLevel[world]', x=-1160.25, y=91.00, z=2848.50, removed=DISCARDED] wasn't found in section class_4076{x=-73, y=5, z=178} (destroying due to DISCARDED)
- `2026-03-10 17:16:43` `disconnect_packet_error` ``: Error sending packet clientbound/minecraft:disconnect
- `2026-03-10 17:17:33` `disconnect_packet_error` ``: Error sending packet clientbound/minecraft:disconnect
- `2026-03-10 17:30:12` `discarded` `Munchlax`: Entity PokemonEntity['Munchlax'/42501, l='ServerLevel[world]', x=-1389.50, y=88.00, z=3564.46, removed=DISCARDED] wasn't found in section class_4076{x=-87, y=5, z=222} (destroying due to DISCARDED)
- `2026-03-10 17:37:41` `cant_keep_up` ``: Can't keep up! Is the server overloaded? Running 2256ms or 45 ticks behind
- `2026-03-10 17:39:43` `disconnect_packet_error` ``: Error sending packet clientbound/minecraft:disconnect
- `2026-03-10 17:44:22` `disconnect` `Totamote`: Totamote lost connection: Disconnected
- `2026-03-10 17:48:05` `disconnect_packet_error` ``: Error sending packet clientbound/minecraft:disconnect
- `2026-03-10 18:01:00` `disconnect_packet_error` ``: Error sending packet clientbound/minecraft:disconnect
- `2026-03-10 18:06:53` `disconnect_packet_error` ``: Error sending packet clientbound/minecraft:disconnect
- `2026-03-10 18:22:45` `disconnect_packet_error` ``: Error sending packet clientbound/minecraft:disconnect
- `2026-03-10 18:29:04` `disconnect_packet_error` ``: Error sending packet clientbound/minecraft:disconnect

## Actions recommandees

- Ouvrir un incident Cobblemon centre sur `removed=DISCARDED` avec les especes et horaires dominants.
- Conserver les warnings de mouvement comme signature secondaire pour corriger le probleme d'entites Cobblemon.
- Traiter `clientbound/minecraft:disconnect` comme bruit reseau secondaire, pas comme cause racine.
