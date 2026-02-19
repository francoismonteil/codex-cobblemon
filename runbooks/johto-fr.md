# Johto (FR)

La map Cobblemon Johto contient beaucoup de textes "en dur" (dialogues/PNJ/tellraw).
La langue du client ne suffit pas pour tout traduire.

On utilise donc un datapack de traduction **partiel** qui override uniquement certains fichiers.

## Etat actuel
- Datapack: `data/world/datapacks/JohtoFR`
- Scope: New Bark Town (zone de depart) pour commencer.

## Plan (roadmap)
Objectif: traduire en priorite ce que les joueurs voient le plus, sans casser les scripts/PNJ.

1) Base technique (deja en place)
- Un datapack `JohtoFR` qui override des fichiers de dialogues.
- Un generateur: `infra/johto-fr-generate.sh` + un `reload`.

2) Traduction "zone par zone" (ordre recommande)
- New Bark Town (fait).
- Cherrygrove City + Route 29/30 (prochaine).
- Violet City + Sprout Tower.
- Azalea Town + Slowpoke Well.
- Goldenrod City (gros morceau: shops, events, dialogues).
- Ecruteak / Olivine / Cianwood / Blackthorn + postgame.

3) Couvrir les 3 types de textes
- Dialogues Cobblemon (`data/cobblemon/dialogues/**/*.json`) : priorite.
- Messages `tellraw` dans les `.mcfunction` (plus delicat: JSON dans commande).
- Panneaux/livres/texte "dans le monde" (a traiter au cas par cas).

4) Qualite / securite
- Ne jamais traduire les champs de commande/scripts (actions `q.*`, fonctions, IDs).
- Ne traduire que les champs "texte" (`lines`, `options[].text`, etc.).
- Après chaque ajout: `reload` + verification logs (pas d'erreur JSON / datapack).

5) Mode operatoire (iteration)
- Choisir une zone.
- Extraire les strings (liste des lignes + boutons).
- Traduire et regen le datapack.
- Test en jeu (parcours + 2-3 PNJ cles).

## Generer / mettre a jour la traduction
Sur le serveur:
```bash
cd <MC_PROJECT_DIR>
./infra/johto-fr-generate.sh
```

Verifier:
```bash
./infra/mc.sh "datapack list"
```

## Extension
Pour avancer, on ajoute d'autres zones (Cherrygrove, Violet, etc.) dans le generateur.
