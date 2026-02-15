Versions verrouillees pour un serveur Cobblemon (modpack officiel, Modrinth)

- Minecraft: 1.21.1
- Loader: Fabric (version non fournie dans le manifest Modrinth v2/version/Lydu1ZNo)
- Fabric API: non fournie dans le manifest Modrinth v2/version/Lydu1ZNo
- Java: 21 (derive de Minecraft 1.21.1; source: Mojang Help Center "Minecraft Java Edition Requirements" indiquant Java 21 pour 1.20.5+)
- Modpack: Cobblemon Official Modpack [Fabric] 1.7.3
  - Modrinth project id: 5FFgwNNP
  - Modrinth version id: Lydu1ZNo

Fichier primaire du modpack (mrpack)

- File id: qzDA6ExO
- Filename: Cobblemon Modpack [Fabric] 1.7.3.mrpack
- URL: https://cdn.modrinth.com/data/5FFgwNNP/versions/Lydu1ZNo/Cobblemon%20Modpack%20%5BFabric%5D%201.7.3.mrpack
- Size: 101013638
- SHA1: e8a140c53495b3238287b8b0e5ae4359ad578be7
- SHA512: c74ae4cab42ca3d76238e7615d8f82bc648c7afcf76184253e8bd28aca8587121dea0cc46af47b4c88e809749a42430f3016f96290cff5537d0fe5347641d4d2

Dependencies (embedded)

- 76 dependances embedded referencees par le manifest Modrinth (voir modpack/mods.list.md).

Variables utiles pour l'infrastructure Docker / installation Modrinth

- MODRINTH_PROJECT_ID: 5FFgwNNP
- MODRINTH_VERSION_ID: Lydu1ZNo
- MODRINTH_FILE_ID: qzDA6ExO
- MODRINTH_FILE_SHA1: e8a140c53495b3238287b8b0e5ae4359ad578be7
- MODRINTH_FILE_SHA512: c74ae4cab42ca3d76238e7615d8f82bc648c7afcf76184253e8bd28aca8587121dea0cc46af47b4c88e809749a42430f3016f96290cff5537d0fe5347641d4d2
- MODRINTH_API_BASE: https://api.modrinth.com
- DOWNLOAD_DIR: /data/mods
- MC_VERSION: 1.21.1
- JAVA_VERSION: 21

Notes sur la compatibilite et sources

1. Source verrouillee
   - Modrinth modpack: "Cobblemon Official Modpack [Fabric]" version 1.7.3
   - Version ID: Lydu1ZNo
   - Project ID: 5FFgwNNP

2. Java
   - Le manifest ne fournit pas de version Java explicite. Le runtime Java 21 est derive de la politique Mojang pour les versions 1.20.5+ (incluant 1.21.1).
   - Source: https://help.minecraft.net/hc/en-us/articles/4409225939853-Minecraft-Java-Edition-Requirements

3. Loader et Fabric API
   - Le manifest Modrinth v2/version/Lydu1ZNo ne fournit pas les versions precises du loader ou de Fabric API. Elles doivent etre extraites depuis le contenu du .mrpack (manifest interne) pour un verrouillage total.

Checklist de verification (operateur)

- [ ] Extraire le manifest interne du .mrpack et pinner les versions exactes du Fabric Loader et de Fabric API.
- [ ] Verifier que le runtime Java 21 est accepte par toutes les dependances cote serveur.
