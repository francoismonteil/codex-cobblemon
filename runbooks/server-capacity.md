# Capacites serveur (Linux)

Ce document persiste un snapshot des capacites materielle/OS du serveur Minecraft (host Linux).
Il ne doit pas contenir de secrets (ex: webhook, mots de passe, tokens).

## Cible
- Host: `<MC_SERVER_HOST>` (voir `runbooks/site.local.md`)
- Utilisateur SSH: `<MC_SSH_USER>`
- Repo sur le serveur: `<MC_PROJECT_DIR>` (example: `/home/linux/codex-cobblemon`)

## Snapshot 2026-02-13T06:24:50-06:00

### Plateforme
- Machine: ASUSTeK COMPUTER INC. `K75VJ`
- Virtualisation: `none` (bare metal)
- OS: Debian GNU/Linux 13.3 (trixie)
- Noyau: Linux 6.12.69+deb13-amd64 (build Debian 6.12.69-1, 2026-02-08)
- Uptime au moment du releve: ~15h

### CPU (capacite totale)
- Modele: Intel(R) Core(TM) i7-3630QM CPU @ 2.40GHz
- Coeurs/threads: 4 c / 8 threads
- Frequences annoncees: 1.2 GHz min / 3.4 GHz max

### Memoire (capacite totale)
- RAM: 7.6 GiB (au moment du releve: ~4.2 GiB utilises, ~3.5 GiB disponibles)
- Swap: 7.9 GiB (au moment du releve: ~2.2 GiB utilises)
  - Swap device: `/dev/sda5` (partition)
  - Note: `swapon` non installe, infos lues via `/proc/swaps`.

### Stockage (capacite totale)
- SSD systeme: Samsung SSD 850 EVO 250GB (`sda`, 232.9G)
  - `/` (ext4): 221G (au moment du releve: 13G utilises, 197G libres)
  - swap: 7.9G (sda5)
- Disque backups: ST1000LM024 (`sdb`, 931.5G, rota=1)
  - `/mnt/backup2` (ext4): 916G (au moment du releve: 1.2G utilises, 869G libres)

### Reseau
- Interface active: `wlp3s0` (Wi-Fi)
- IP LAN: `<MC_SERVER_LAN_IP>/<CIDR>` (ex: `192.0.2.10/24`)
- Ports en ecoute (host):
  - `22/tcp` (SSH)
  - `25565/tcp` (Minecraft)

### Docker / Minecraft (contexte capacite stack)
- Docker: 29.2.1
- Docker Compose: v5.0.2
- Service: `cobblemon`
  - Etat: `healthy`
  - Ports: `0.0.0.0:25565->25565/tcp` et `[::]:25565->25565/tcp`
  - Conso a l'instant T (docker stats): ~3.36 GiB RAM (~43.9% du host), CPU ~12.5% (instantane)

### Parametres Minecraft (snapshot, sans secrets)
- `.env`:
  - `MEMORY=4608M`
  - `USE_AIKAR_FLAGS=true`
  - `ENABLE_RCON=false`
- `data/server.properties`:
  - `server-port=25565`
  - `online-mode=true`
  - `max-players=6`
  - `view-distance=8`
  - `simulation-distance=7`

## Commandes (reproductibles)
Commande (depuis poste admin Windows) utilisee pour collecter les infos:

```powershell
$key="<SSH_KEY_MAIN>"
ssh -i $key -o BatchMode=yes -o StrictHostKeyChecking=accept-new <MC_SSH_USER>@<MC_SERVER_HOST> `
  "hostnamectl; cat /etc/os-release; uname -a; uptime; systemd-detect-virt; lscpu; free -h; cat /proc/swaps; df -hT; lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT,ROTA,MODEL; ip -br addr; ss -lnt; docker --version; docker compose version; cd <MC_PROJECT_DIR> && docker compose ps cobblemon && docker stats --no-stream cobblemon"
```
