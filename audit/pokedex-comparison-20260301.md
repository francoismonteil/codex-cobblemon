# Rapport Pokedex serveur - 2026-03-01

## Perimetre

- Source joueurs: `data/world/pokedex/<uuid>.nbt`
- Source temps de jeu: `data/world/stats/<uuid>.json`
- Base complete des especes: `data/showdown/data/pokedex.js`
- Joueurs analyses: `Sondoku`, `TiidyMan`, `Totamote`

Definitions:
- `seen` = espece marquee `ENCOUNTERED` ou `CAUGHT` dans le Pokedex serveur.
- `caught` = espece marquee `CAUGHT`.
- `encountered_only` = vue mais pas capturee.
- `play_time` = statistique vanilla `minecraft:play_time`, convertie en heures.

## Vue d'ensemble

- Especes implementees dans la stack: `1024`
- Especes deja vues sur le serveur (union des 3 joueurs): `310` soit `30.27%`
- Especes deja capturees sur le serveur (union des 3 joueurs): `208` soit `20.31%`

| Joueur | Temps de jeu (h) | Vues | % du monde vu | % du roster total | Vues/h | Capturees | % du monde capture | % du roster total | Capt./h | Combats |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Sondoku | 49.43 | 193 | 62.26% | 18.85% | 3.90 | 83 | 39.90% | 8.11% | 1.68 | 366 |
| TiidyMan | 42.14 | 140 | 45.16% | 13.67% | 3.32 | 77 | 37.02% | 7.52% | 1.83 | 162 |
| Totamote | 39.07 | 170 | 54.84% | 16.60% | 4.35 | 124 | 59.62% | 12.11% | 3.17 | 232 |

Lecture rapide:
- `Sondoku` a la meilleure couverture brute en `seen` avec plus de temps de jeu.
- `Totamote` a la meilleure progression relative par heure, en `seen/h` et surtout en `caught/h`.
- `TiidyMan` est derriere en couverture brute et en `seen/h`, mais reste proche de `Sondoku` en `caught/h`.

## Liste exhaustive du monde

### World seen union

`aipom, ambipom, ampharos, araquanid, arbok, arcanine, ariados, aron, azurill, banette, barbaracle, basculin, beedrill, bellsprout, bidoof, blitzle, boldore, boltund, bonsly, bouffalant, bramblin, buizel, bulbasaur, bunnelby, butterfree, cacturne, capsakid, carbink, carvanha, caterpie, centiskorch, chandelure, chewtle, cinccino, clauncher, combee, corphish, corsola, corviknight, corvisquire, cottonee, crabrawler, cramorant, croagunk, cubone, cyclizar, cyndaquil, dachsbun, darumaka, deerling, dewpider, diggersby, diglett, ditto, doduo, drednaw, drilbur, drowzee, dubwool, ducklett, dugtrio, duosion, durant, duskull, dwebble, eevee, electabuzz, electrike, elekid, emolga, exeggcute, farigiraf, fearow, fidough, flaaffy, flabebe, flamigo, fletchinder, fletchling, flittle, floatzel, fomantis, frillish, froakie, frogadier, furfrou, furret, gabite, galvantula, garbodor, garchomp, gastly, gengar, geodude, gible, gigalith, gimmighoul, girafarig, glameow, gligar, gloom, golbat, goldeen, golduck, granbull, graveler, greedent, greninja, grimer, grookey, grotle, growlithe, gumshoos, gurdurr, gyarados, haunter, herdier, hippopotas, hoothoot, hoppip, houndour, hypno, igglybuff, illumise, impidimp, inkay, jigglypuff, joltik, kadabra, kakuna, kilowattrel, klawf, klink, koffing, krabby, lairon, lampent, lapras, larvesta, lechonk, ledian, ledyba, lickilicky, lickitung, liepard, lillipup, linoone, litleo, litwick, mabosstiff, magby, magcargo, magikarp, magnemite, manectric, mankey, maractus, mareanie, mareep, marill, maschiff, masquerain, meowstic, meowth, metapod, mightyena, miltank, mimejr, minccino, minun, misdreavus, morgrem, morpeko, mudbray, munna, musharna, nacli, natu, nickit, nidoranf, nidoranm, noivern, nosepass, numel, oddish, oinkologne, orthworm, panpour, pansage, pansear, patrat, persian, petilil, phanpy, pichu, pidgeot, pidgeotto, pidgey, pidove, pignite, pikachu, pikipek, plusle, politoed, poliwag, poliwhirl, ponyta, poochyena, primeape, psyduck, purrloin, purugly, pyroar, quilava, rapidash, raticate, rattata, rellor, remoraid, rhyhorn, rillaboom, riolu, roggenrola, rookidee, salandit, sandshrew, sandslash, sandygast, sawsbuck, scatterbug, scraggy, scyther, seaking, seedot, sentret, sewaddle, sharpedo, shinx, shroomish, shuppet, silicobra, simisage, sinistea, sizzlipede, skarmory, skiploom, skorupi, skwovet, slakoth, slowbro, slowpoke, slugma, smeargle, snubbull, solosis, solrock, spearow, spinarak, spiritomb, squawkabilly, steenee, stonjourner, swanna, swellow, tadbulb, taillow, talonflame, tandemaus, tangrowth, tauros, teddiursa, tentacool, tentacruel, thwackey, timburr, tinkatink, torkoal, toxel, toxicroak, tranquill, trubbish, trumbeak, turtwig, typhlosion, umbreon, veluza, venipede, victreebel, vileplume, vivillon, voltorb, vulpix, watchog, wattrel, weedle, weepinbell, whimsicott, whirlipede, whismur, wiglett, woobat, wooloo, wyrdeer, yamper, yanma, yungoos, zebstrika, zigzagoon, zorua, zubat`

### World caught union

`aipom, ampharos, arbok, arcanine, ariados, aron, azurill, barbaracle, bellsprout, blitzle, boldore, boltund, bonsly, bouffalant, bramblin, buizel, bulbasaur, butterfree, capsakid, carbink, carvanha, caterpie, chandelure, chewtle, cinccino, corphish, corviknight, corvisquire, cottonee, croagunk, cubone, cyclizar, cyndaquil, deerling, diglett, ditto, drilbur, drowzee, duosion, durant, duskull, dwebble, eevee, electabuzz, electrike, elekid, emolga, exeggcute, fearow, flaaffy, flamigo, fletchinder, fletchling, fomantis, froakie, frogadier, furfrou, gabite, galvantula, garchomp, gastly, gengar, geodude, gible, gigalith, girafarig, gloom, golbat, graveler, greedent, greninja, grimer, grookey, grotle, growlithe, gurdurr, gyarados, haunter, hoothoot, hoppip, houndour, hypno, igglybuff, impidimp, jigglypuff, joltik, kilowattrel, klawf, klink, koffing, krabby, lairon, lampent, larvesta, ledian, liepard, lillipup, linoone, litleo, litwick, mabosstiff, magby, magcargo, magikarp, magnemite, manectric, mankey, mareep, maschiff, meowstic, meowth, metapod, miltank, minccino, minun, misdreavus, munna, musharna, natu, nidoranf, nidoranm, numel, oddish, oinkologne, pansage, pansear, patrat, persian, petilil, phanpy, pichu, pidgeotto, pidgey, pidove, pignite, pikachu, pikipek, plusle, poliwag, ponyta, poochyena, purugly, quilava, rapidash, rattata, rhyhorn, rillaboom, riolu, roggenrola, rookidee, salandit, sandshrew, sawsbuck, scatterbug, scyther, seedot, sentret, sewaddle, shinx, shroomish, shuppet, simisage, sizzlipede, skarmory, skiploom, slakoth, slowpoke, slugma, smeargle, snubbull, solosis, spearow, spinarak, squawkabilly, steenee, stonjourner, tadbulb, taillow, talonflame, tandemaus, tauros, teddiursa, thwackey, timburr, torkoal, toxel, toxicroak, tranquill, trumbeak, turtwig, typhlosion, venipede, victreebel, vileplume, vivillon, vulpix, watchog, weedle, weepinbell, whirlipede, whismur, woobat, wyrdeer, yungoos, zebstrika, zigzagoon, zorua, zubat`

## Par joueur

### Sondoku

- Temps de jeu: `49.43 h`
- Especes vues: `193`
- Especes capturees: `83`
- Especes vues seulement: `110`
- Couverture du monde vu: `62.26%`
- Couverture du monde capture: `39.90%`
- Couverture du roster complet: `18.85%` vu, `8.11%` capture
- Rythme: `3.90` especes vues/h, `1.68` especes capturees/h

#### Seen

`aipom, ampharos, arcanine, barbaracle, basculin, bellsprout, bidoof, blitzle, boldore, boltund, bonsly, bouffalant, bramblin, buizel, bunnelby, butterfree, caterpie, cinccino, combee, corphish, corviknight, corvisquire, cottonee, crabrawler, cramorant, dachsbun, darumaka, deerling, dewpider, diggersby, diglett, doduo, drednaw, drilbur, drowzee, dubwool, ducklett, dugtrio, dwebble, eevee, electabuzz, electrike, elekid, fearow, fidough, flaaffy, flabebe, flittle, frillish, furfrou, furret, gabite, garbodor, garchomp, gastly, geodude, gible, gimmighoul, girafarig, glameow, goldeen, golduck, granbull, graveler, greedent, grimer, grookey, growlithe, gumshoos, gyarados, hoothoot, hoppip, houndour, igglybuff, illumise, impidimp, inkay, joltik, kadabra, kilowattrel, koffing, krabby, lapras, lechonk, ledian, ledyba, lickitung, lillipup, linoone, litleo, mabosstiff, magby, magikarp, magnemite, manectric, mankey, mareep, marill, maschiff, masquerain, meowth, miltank, minccino, minun, mudbray, nickit, nidoranf, numel, oddish, oinkologne, panpour, pansage, patrat, persian, petilil, phanpy, pichu, pidgeotto, pidgey, pidove, pikachu, pikipek, poliwag, ponyta, poochyena, psyduck, purrloin, purugly, rapidash, rattata, rellor, remoraid, rillaboom, riolu, roggenrola, rookidee, salandit, sandshrew, sandslash, sandygast, sawsbuck, scatterbug, scraggy, seaking, seedot, sentret, sewaddle, sharpedo, shuppet, sinistea, skiploom, skorupi, skwovet, slakoth, slowpoke, slugma, smeargle, snubbull, solosis, solrock, spearow, spinarak, spiritomb, squawkabilly, stonjourner, swanna, swellow, tadbulb, taillow, tauros, teddiursa, tentacool, thwackey, timburr, tinkatink, torkoal, tranquill, trubbish, veluza, vivillon, voltorb, vulpix, watchog, wattrel, weedle, woobat, wyrdeer, yamper, yanma, yungoos, zebstrika, zigzagoon, zubat`

#### Caught

`ampharos, arcanine, barbaracle, blitzle, boldore, boltund, bonsly, bramblin, buizel, cinccino, corviknight, corvisquire, deerling, drilbur, drowzee, eevee, electabuzz, elekid, fearow, flaaffy, gabite, garchomp, geodude, gible, girafarig, graveler, greedent, grimer, grookey, growlithe, gyarados, hoothoot, houndour, kilowattrel, lillipup, linoone, litleo, mabosstiff, magby, magikarp, magnemite, mareep, maschiff, nidoranf, oddish, patrat, persian, petilil, phanpy, pichu, pidove, pikachu, pikipek, ponyta, poochyena, rapidash, rattata, rillaboom, riolu, roggenrola, rookidee, sandshrew, scatterbug, seedot, sewaddle, skiploom, slakoth, slowpoke, slugma, smeargle, spinarak, squawkabilly, tadbulb, thwackey, torkoal, tranquill, vulpix, watchog, woobat, wyrdeer, yungoos, zigzagoon, zubat`

#### Encountered only

`aipom, basculin, bellsprout, bidoof, bouffalant, bunnelby, butterfree, caterpie, combee, corphish, cottonee, crabrawler, cramorant, dachsbun, darumaka, dewpider, diggersby, diglett, doduo, drednaw, dubwool, ducklett, dugtrio, dwebble, electrike, fidough, flabebe, flittle, frillish, furfrou, furret, garbodor, gastly, gimmighoul, glameow, goldeen, golduck, granbull, gumshoos, hoppip, igglybuff, illumise, impidimp, inkay, joltik, kadabra, koffing, krabby, lapras, lechonk, ledian, ledyba, lickitung, manectric, mankey, marill, masquerain, meowth, miltank, minccino, minun, mudbray, nickit, numel, oinkologne, panpour, pansage, pidgeotto, pidgey, poliwag, psyduck, purrloin, purugly, rellor, remoraid, salandit, sandslash, sandygast, sawsbuck, scraggy, seaking, sentret, sharpedo, shuppet, sinistea, skorupi, skwovet, snubbull, solosis, solrock, spearow, spiritomb, stonjourner, swanna, swellow, taillow, tauros, teddiursa, tentacool, timburr, tinkatink, trubbish, veluza, vivillon, voltorb, wattrel, weedle, yamper, yanma, zebstrika`

### TiidyMan

- Temps de jeu: `42.14 h`
- Especes vues: `140`
- Especes capturees: `77`
- Especes vues seulement: `63`
- Couverture du monde vu: `45.16%`
- Couverture du monde capture: `37.02%`
- Couverture du roster complet: `13.67%` vu, `7.52%` capture
- Rythme: `3.32` especes vues/h, `1.83` especes capturees/h

#### Seen

`aipom, ambipom, ampharos, araquanid, arbok, ariados, aron, azurill, beedrill, bellsprout, blitzle, boldore, bouffalant, buizel, butterfree, cacturne, capsakid, carvanha, caterpie, chewtle, clauncher, combee, corphish, corsola, cottonee, cyclizar, cyndaquil, diglett, ditto, durant, dwebble, eevee, electabuzz, electrike, elekid, farigiraf, fearow, fidough, flaaffy, fletchling, floatzel, fomantis, galvantula, garbodor, gastly, geodude, glameow, graveler, growlithe, gurdurr, haunter, hoothoot, hoppip, houndour, igglybuff, impidimp, jigglypuff, joltik, kakuna, kilowattrel, klawf, koffing, krabby, lairon, lapras, larvesta, lechonk, ledian, lickitung, lillipup, magikarp, manectric, mankey, maractus, mareanie, mareep, maschiff, meowth, metapod, mightyena, miltank, minun, morgrem, mudbray, munna, nacli, natu, nickit, oddish, orthworm, patrat, phanpy, pichu, pidgeot, pidgeotto, pidgey, pignite, pikipek, politoed, poliwag, ponyta, poochyena, quilava, roggenrola, rookidee, sandshrew, scatterbug, sentret, sharpedo, shuppet, silicobra, sizzlipede, skarmory, skiploom, slowbro, slowpoke, solosis, spearow, spinarak, squawkabilly, stonjourner, taillow, tandemaus, tentacool, tentacruel, toxel, typhlosion, victreebel, vivillon, voltorb, watchog, weedle, weepinbell, whimsicott, whirlipede, wiglett, woobat, wooloo, yungoos, zebstrika`

#### Caught

`arbok, ariados, aron, azurill, bellsprout, blitzle, boldore, bouffalant, capsakid, carvanha, corphish, cyclizar, cyndaquil, diglett, ditto, dwebble, eevee, electabuzz, electrike, elekid, fearow, flaaffy, fletchling, fomantis, galvantula, gastly, geodude, graveler, growlithe, haunter, hoothoot, hoppip, houndour, igglybuff, impidimp, joltik, kilowattrel, klawf, koffing, krabby, lairon, larvesta, ledian, magikarp, manectric, mareep, maschiff, meowth, metapod, miltank, minun, munna, phanpy, pichu, pidgey, pignite, poliwag, poochyena, quilava, roggenrola, rookidee, sandshrew, scatterbug, shuppet, sizzlipede, solosis, spearow, spinarak, squawkabilly, stonjourner, toxel, typhlosion, victreebel, vivillon, weedle, weepinbell, zebstrika`

#### Encountered only

`aipom, ambipom, ampharos, araquanid, beedrill, buizel, butterfree, cacturne, caterpie, chewtle, clauncher, combee, corsola, cottonee, durant, farigiraf, fidough, floatzel, garbodor, glameow, gurdurr, jigglypuff, kakuna, lapras, lechonk, lickitung, lillipup, mankey, maractus, mareanie, mightyena, morgrem, mudbray, nacli, natu, nickit, oddish, orthworm, patrat, pidgeot, pidgeotto, pikipek, politoed, ponyta, sentret, sharpedo, silicobra, skarmory, skiploom, slowbro, slowpoke, taillow, tandemaus, tentacool, tentacruel, voltorb, watchog, whimsicott, whirlipede, wiglett, woobat, wooloo, yungoos`

### Totamote

- Temps de jeu: `39.07 h`
- Especes vues: `170`
- Especes capturees: `124`
- Especes vues seulement: `46`
- Couverture du monde vu: `54.84%`
- Couverture du monde capture: `59.62%`
- Couverture du roster complet: `16.60%` vu, `12.11%` capture
- Rythme: `4.35` especes vues/h, `3.17` especes capturees/h

#### Seen

`aipom, arcanine, aron, banette, bellsprout, boldore, bouffalant, bramblin, buizel, bulbasaur, butterfree, carbink, caterpie, centiskorch, chandelure, chewtle, cottonee, croagunk, cubone, cyclizar, cyndaquil, dachsbun, darumaka, deerling, diggersby, doduo, drilbur, drowzee, ducklett, duosion, durant, duskull, eevee, electabuzz, elekid, emolga, exeggcute, flaaffy, flamigo, fletchinder, fletchling, froakie, frogadier, furfrou, furret, galvantula, gastly, gengar, geodude, gigalith, girafarig, gligar, gloom, golbat, greninja, grimer, grotle, growlithe, gurdurr, haunter, herdier, hippopotas, hoppip, houndour, hypno, jigglypuff, joltik, kakuna, klink, koffing, lairon, lampent, larvesta, lechonk, ledian, ledyba, lickilicky, liepard, linoone, litleo, litwick, mabosstiff, magby, magcargo, mankey, mareep, meowstic, meowth, miltank, mimejr, minccino, misdreavus, morpeko, mudbray, munna, musharna, natu, nidoranm, noivern, nosepass, numel, oddish, oinkologne, pansage, pansear, persian, petilil, pichu, pidgeotto, pidgey, pidove, pignite, plusle, poliwhirl, ponyta, primeape, purugly, pyroar, rapidash, raticate, rhyhorn, rookidee, salandit, sandshrew, sawsbuck, scyther, seedot, sentret, sewaddle, shinx, shroomish, shuppet, simisage, sizzlipede, skarmory, skiploom, skwovet, slakoth, slowbro, slowpoke, snubbull, solosis, spinarak, spiritomb, squawkabilly, steenee, taillow, talonflame, tandemaus, tangrowth, tauros, teddiursa, timburr, torkoal, toxicroak, trumbeak, turtwig, umbreon, venipede, vileplume, vivillon, vulpix, weepinbell, whimsicott, whirlipede, whismur, woobat, wooloo, zorua, zubat`

#### Caught

`aipom, arcanine, aron, bellsprout, boldore, bouffalant, bramblin, bulbasaur, butterfree, carbink, caterpie, chandelure, chewtle, cottonee, croagunk, cubone, cyclizar, cyndaquil, deerling, drilbur, drowzee, duosion, durant, duskull, eevee, electabuzz, emolga, exeggcute, flaaffy, flamigo, fletchinder, fletchling, froakie, frogadier, furfrou, gastly, gengar, geodude, gigalith, girafarig, gloom, golbat, greninja, grimer, grotle, growlithe, gurdurr, haunter, houndour, hypno, jigglypuff, joltik, klink, lairon, lampent, larvesta, liepard, litwick, mabosstiff, magcargo, mankey, mareep, meowstic, meowth, miltank, minccino, misdreavus, munna, musharna, natu, nidoranm, numel, oddish, oinkologne, pansage, pansear, persian, petilil, pichu, pidgeotto, pidgey, pidove, pignite, plusle, purugly, rapidash, rhyhorn, rookidee, salandit, sandshrew, sawsbuck, scyther, seedot, sentret, sewaddle, shinx, shroomish, shuppet, simisage, skarmory, slakoth, slowpoke, snubbull, spinarak, steenee, taillow, talonflame, tandemaus, tauros, teddiursa, timburr, torkoal, toxicroak, trumbeak, turtwig, venipede, vileplume, vivillon, vulpix, weepinbell, whirlipede, whismur, zorua, zubat`

#### Encountered only

`banette, buizel, centiskorch, dachsbun, darumaka, diggersby, doduo, ducklett, elekid, furret, galvantula, gligar, herdier, hippopotas, hoppip, kakuna, koffing, lechonk, ledian, ledyba, lickilicky, linoone, litleo, magby, mimejr, morpeko, mudbray, noivern, nosepass, poliwhirl, ponyta, primeape, pyroar, raticate, sizzlipede, skiploom, skwovet, slowbro, solosis, spiritomb, squawkabilly, tangrowth, umbreon, whimsicott, woobat, wooloo`
