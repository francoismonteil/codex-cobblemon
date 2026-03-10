# Dossier Cobblemon: stabilite des entites

Fenetre:
- `2026-03-08` au `2026-03-10`
- source: logs serveur distants via `tools/server_log_digest.py`

## Conclusion

- Le probleme principal restant n'est plus la RAM hote.
- Le signal dominant est un probleme Cobblemon de cycle de vie / synchronisation d'entites.
- Le `8 mars 2026`, le probleme a une forme "monture rapide":
  - `Garchomp (vehicle of Sondoku) moved too quickly!`
  - `watchdog`
  - `Garchomp ... removed=DISCARDED`
- Le `10 mars 2026`, le probleme persiste sous une forme plus large:
  - beaucoup de `removed=DISCARDED`
  - presque pas de lag
  - pas de `moved too quickly!`
  - donc le bug ne depend pas uniquement d'un vol rapide sur monture

## Faits consolides

- sur `2026-03-08` a `2026-03-10`:
  - `watchdog`: `1`
  - `cant_keep_up`: `19`
  - `moved_too_quickly`: `106`
  - `moved_wrongly`: `4`
  - `discarded`: `64`
- acteurs dominants de mouvement:
  - `Garchomp (vehicle of Sondoku)`: `102`
  - `Sondoku`: `5`
  - `Totamote`: `3`
- especes les plus touchees par `removed=DISCARDED`:
  - `Volcarona`: `23`
  - `Munchlax`: `17`
  - `Garchomp`: `7`
  - `Blaziken`: `7`
  - `Rillaboom`: `3`
  - `Aerodactyl`: `3`

## Focus 8 mars 2026

- point haut critique:
  - `watchdog`: `1`
  - `moved_too_quickly`: rafales massives, quasi exclusivement `Garchomp (vehicle of Sondoku)`
- lecture:
  - forme la plus severe du bug
  - corrigee partiellement par la baseline actuelle sur la partie lag/crash, mais pas sur la partie entites

## Focus 10 mars 2026

- etat serveur:
  - conteneur `healthy`
  - `cant_keep_up`: `2`
  - `watchdog`: `0`
  - `moved_too_quickly`: `0`
  - `moved_wrongly`: `3`
  - `discarded`: `54`
- joueurs visibles:
  - `Totamote`
  - `TiidyMan`
- especes les plus touchees:
  - `Volcarona`: `23`
  - `Munchlax`: `17`
  - `Blaziken`: `7`
  - `Aerodactyl`: `3`
- repartition horaire `discarded`:
  - `2026-03-10 15`: `26`
  - `2026-03-10 16`: `15`
  - `2026-03-10 17`: `6`
- lecture:
  - la panne ne se limite plus a `Garchomp`
  - elle ne se limite plus non plus a un contexte de lag extreme
  - elle semble suivre l'activite joueur/exploration plus que la seule saturation serveur

## Indices utiles

- le `10 mars 2026`, plusieurs `removed=DISCARDED` recents sont observes vers:
  - `x~-1112..-1559`
  - `z~2674..3564`
- inference:
  - il existe probablement une zone ou un style d'exploration qui augmente le volume d'entites Cobblemon detruites
  - ce point doit etre verifie, mais ce n'est pas encore une preuve de causalite

## Ce qui est ecarte ou affaibli

- manque de RAM hote comme cause principale
  - affaibli
  - depuis `16 Go` host et `6G` heap, le serveur reste stable cote OS
- `Distant Horizons` comme cause unique
  - ecarte
  - le bug d'entites persiste en `PRE_EXISTING_ONLY`
- `Lithium` comme cause principale
  - affaibli
  - le test A/B sur collisions n'a pas supprime le symptome

## Actions recommandees

- conserver la baseline actuelle sans nouveau changement de performance
- relever chaque jour:
  - `cant_keep_up`
  - `discarded`
  - `moved_too_quickly`
  - `moved_wrongly`
- preparer un ticket Cobblemon avec:
  - le crash watchdog du `2026-03-08 13:41`
  - les rafales `Garchomp (vehicle of Sondoku) moved too quickly!`
  - la persistance `removed=DISCARDED` sur `Volcarona`, `Munchlax`, `Blaziken`, `Aerodactyl`
  - les exemples de `Totamote moved wrongly!`
- si le volume `discarded` reste eleve pendant plusieurs jours:
  - ajouter une capture plus fine des coordonnees et especes pour identifier un pattern de zone

## Preuves de reference

- [server-log-digest-20260308-20260310.json](d:\Dev\Projet prokerplanning\codex-cobblemon\audit\server-log-digest-20260308-20260310.json)
- [server-log-digest-20260310.json](d:\Dev\Projet prokerplanning\codex-cobblemon\audit\server-log-digest-20260310.json)
- [stability-audit-20260308.md](d:\Dev\Projet prokerplanning\codex-cobblemon\audit\stability-audit-20260308.md)
