# Runbook: Setup SSH distant

## Objectif
Installer une machine Linux administrable en SSH pour heberger ce serveur Minecraft.

## 1) Preparation machine (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install -y ca-certificates curl git ufw
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
newgrp docker
docker --version
docker compose version
```

## 2) Hardening SSH de base
```bash
mkdir -p ~/.ssh && chmod 700 ~/.ssh
echo "<YOUR_PUBLIC_KEY>" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

Puis config SSH:
```text
PasswordAuthentication no
PubkeyAuthentication yes
PermitRootLogin no
```

```bash
sudo systemctl restart ssh
```

## 3) Regles reseau
```bash
sudo ufw allow 22/tcp
sudo ufw allow 25565/tcp
sudo ufw enable
sudo ufw status
```

## 4) Deploiement repo
```bash
sudo mkdir -p <MC_PROJECT_DIR>
sudo chown -R $USER:$USER <MC_PROJECT_DIR>
cd <MC_PROJECT_DIR>
git clone <YOUR_REPO_URL> .
cp .env.example .env
chmod +x infra/*.sh
```

## 5) Demarrage et verification
```bash
./infra/start.sh
docker compose ps
./infra/logs.sh
```

Le serveur doit etre joignable sur `<server-ip>:25565`.

## 6) Exploitation quotidienne
```bash
./infra/logs.sh
./infra/backup.sh
./infra/monitor.sh
./infra/stop.sh
./infra/start.sh
```

Restauration:
```bash
./infra/restore.sh backups/backup-YYYYMMDD-HHMMSS.tar.gz
```

## 7) Notes
- Les details de prod (IP, cles, cron, tuning) sont dans `runbooks/ops-notes.md`.
