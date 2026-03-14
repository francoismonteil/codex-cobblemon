# Incident Carry On `sync_carry_data` - 2026-03-12

Resume:
- incident multijoueur reproductible sur `Carry On 2.2.4.4`
- deconnexion simultanee de plusieurs joueurs
- erreur precise cote serveur et client:
  - `Failed to encode packet 'clientbound/minecraft:custom_payload' (carryon:sync_carry_data)`
- l'incident ne doit plus etre traite comme simple `disconnect_packet_error`

## Environnement confirme

- Minecraft: `1.21.1`
- Fabric Loader: `0.18.4`
- Fabric API: `0.116.8+1.21.1`
- Carry On: `2.2.4.4`
- Cobblemon: `1.7.3+1.21.1`
- contexte: serveur dedie multijoueur

Sources locales:
- client:
  - `C:\Users\Black\AppData\Roaming\ModrinthApp\profiles\Cobblemon Official Modpack [Fabric] (1)\logs\latest.log`
  - `C:\Users\Black\AppData\Roaming\ModrinthApp\profiles\Cobblemon Official Modpack [Fabric] (1)\logs\launcher_log.txt`
- serveur:
  - `docker logs cobblemon`

## Reproductions confirmees

Client:
- `21:07:22`
- `21:50:24`
- `22:03:13`
- `22:05:54`
- `22:07:38`

Serveur:
- `21:07:21`
- `21:50:22`
- `22:03:11`
- `22:05:51`
- `22:07:36`

Joueurs ejectes en meme temps observes dans les logs serveur:
- `21:50:22`: `Sondoku`, `TiidyMan`
- `22:03:11`: `Sondoku`, `TiidyMan`, `Totamote`
- `22:05:51`: `Sondoku`, `TiidyMan`
- `22:07:36`: `Sondoku`, `TiidyMan`

Point encore manquant pour l'upstream:
- l'action gameplay exacte a ete precisee apres coup par l'utilisateur

## Scenario de repro observe

Scenario 1:
- heure: `22:02` locale serveur
- etat:
  - `Sondoku` etait porte par `Totamote`
  - les joueurs touches etaient dans la meme zone de jeu
- action declenchante:
  - le porteur s'accroupit
- resultat:
  - `Sondoku`, `Totamote` et `TiidyMan` sont ejectes

Scenario 2:
- heure: `22:06` locale serveur
- etat:
  - `Sondoku` etait porte par `Ronan`
  - `Totamote` etait dans l'End
- action declenchante:
  - le porteur s'accroupit
- resultat:
  - `Sondoku` et `Ronan` sont ejectes
  - `Totamote`, present dans l'End, n'est pas ejecte

Lecture de ces deux scenarios:
- le declencheur confirme est `player carrying another player` puis `carrier crouches`
- la portee ne semble pas etre strictement serveur globale
- la propagation parait toucher les joueurs presents dans la meme dimension ou la meme zone synchronisee

## Extraits utiles

Client:

```text
[22:03:13] [Render thread/WARN]: Client disconnected with reason: Internal Exception: io.netty.handler.codec.EncoderException: Failed to encode packet 'clientbound/minecraft:custom_payload' (carryon:sync_carry_data)
```

Serveur:

```text
[22:03:11] [Netty Epoll Server IO #15/ERROR]: Error sending packet clientbound/minecraft:custom_payload
io.netty.handler.codec.EncoderException: Failed to encode packet 'clientbound/minecraft:custom_payload' (carryon:sync_carry_data)
Caused by: java.lang.NullPointerException
```

Effets secondaires observes cote serveur:
- `Negative index in crash report handler`
- `Failed to save player data for Totamote`

## Lecture

- la signature utile est `carryon:sync_carry_data`
- l'incident entraine un echec d'encodage reseau cote serveur
- plusieurs joueurs peuvent etre ejectes lors d'une seule occurrence
- le digest actuel du repo agrege une partie de ces incidents sous `disconnect_packet_error`, ce qui masque la cause reelle

## Action upstream recommandee

Issue GitHub cible:
- `https://github.com/Tschipp/CarryOn/issues/926`

Decision recommandee:
- commenter l'issue `#926` avec ces preuves plutot qu'ouvrir tout de suite une nouvelle issue
- si le mainteneur confirme que `#926` est un cas different, reutiliser le brouillon de nouvelle issue dans `audit/carryon-new-issue-draft-20260312.md`
