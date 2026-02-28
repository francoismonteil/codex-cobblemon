# Client Setup (Friends)

## Version a utiliser
Le serveur est configure pour:
- Minecraft **1.21.1**
- Modpack: **Cobblemon Official Modpack [Fabric] 1.7.3**

Si tu installes une autre version (ou si un mod se met a jour tout seul), tu auras des erreurs du type:
`Version mismatch for <mod>`

## Fix rapide "Version mismatch"
Exemple:
`The server expects 21.1.6, but you currently have 21.1.7`

Solution:
- remettre **exactement** la version du mod attendue par le serveur
- ou, plus fiable: installer l'instance du modpack **1.7.3** (et desactiver les auto-updates)

## Conseil
Quand tu invites tes amis, donne leur:
- l'adresse: `<DUCKDNS_DOMAIN>:25565` (voir `runbooks/site.local.md` ou `.env` sur le serveur)
- le modpack exact: **Cobblemon Official Modpack [Fabric] 1.7.3**
- la liste des mods client actuellement attendus: `runbooks/client-pack-recommended.md`
