#!/usr/bin/env bash
set -euo pipefail

# Print shareable connection + client setup info for friends.
#
# Usage:
#   ./infra/friend-info.sh
#   ./infra/friend-info.sh --markdown
#
# Optional .env overrides:
#   FRIENDS_SERVER_ADDRESS=mc.example.org[:25565]   # full address (host or host:port)
#   FRIENDS_MC_PORT=25565
#   FRIENDS_MC_VERSION=1.21.1
#   FRIENDS_MODPACK_NAME="Cobblemon Official Modpack [Fabric]"
#   FRIENDS_MODPACK_VERSION=1.7.3

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${REPO_ROOT}"

if [[ -f "${REPO_ROOT}/.env" ]]; then
  # shellcheck disable=SC1091
  set -a; source "${REPO_ROOT}/.env"; set +a
fi

format="plain"
if [[ "${1:-}" == "--markdown" ]]; then
  format="markdown"
  shift
fi
if [[ $# -ne 0 ]]; then
  echo "Usage: $0 [--markdown]" >&2
  exit 2
fi

normalize_domain() {
  local raw="$1"
  raw="${raw%%,*}"
  if [[ -z "${raw}" ]]; then
    echo ""
    return 0
  fi
  if [[ "${raw}" == *.* ]]; then
    echo "${raw}"
  else
    echo "${raw}.duckdns.org"
  fi
}

address="${FRIENDS_SERVER_ADDRESS:-}"
port="${FRIENDS_MC_PORT:-${MC_PORT:-25565}}"
mc_version="${FRIENDS_MC_VERSION:-1.21.1}"
modpack_name="${FRIENDS_MODPACK_NAME:-Cobblemon Official Modpack [Fabric]}"
modpack_version="${FRIENDS_MODPACK_VERSION:-1.7.3}"

if [[ -z "${address}" ]]; then
  host=""
  if [[ -n "${DUCKDNS_DOMAIN:-}" ]]; then
    host="$(normalize_domain "${DUCKDNS_DOMAIN}")"
  elif [[ -n "${DUCKDNS_DOMAINS:-}" ]]; then
    host="$(normalize_domain "${DUCKDNS_DOMAINS}")"
  fi

  if [[ -n "${host}" ]]; then
    address="${host}:${port}"
  else
    address="<duckdns-domain>.duckdns.org:${port}"
  fi
elif [[ "${address}" != *:* ]]; then
  address="${address}:${port}"
fi

if [[ "${format}" == "markdown" ]]; then
  cat <<EOF
# Infos de connexion

- Adresse serveur: \`${address}\`
- Version Minecraft: \`${mc_version}\`
- Modpack: \`${modpack_name} ${modpack_version}\`
- Important: desactivez les auto-updates de mods (sinon "Version mismatch")
- Guide detaille (repo): \`runbooks/client-setup.md\`

## En cas d'erreur "Version mismatch"

- Revenir exactement a la version attendue par le serveur
- Le plus fiable: reinstaller l'instance du modpack \`${modpack_name} ${modpack_version}\`
EOF
else
  cat <<EOF
Adresse serveur : ${address}
Version Minecraft : ${mc_version}
Modpack : ${modpack_name} ${modpack_version}
Important : desactivez les auto-updates des mods (sinon "Version mismatch")
Guide detaille : runbooks/client-setup.md

En cas de "Version mismatch" :
- remettez exactement la version attendue
- ou reinstallez l'instance du modpack ${modpack_name} ${modpack_version}
EOF
fi
