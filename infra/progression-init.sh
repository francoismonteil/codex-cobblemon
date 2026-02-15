#!/usr/bin/env bash
set -euo pipefail

# Initializes a simple "badges" progression system using vanilla scoreboards.
#
# This is intentionally lightweight (no extra mods/plugins):
# - One objective per badge (0/1)
# - One objective for total badges
#
# Usage:
#   ./infra/progression-init.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

# Best-effort: adding an existing objective prints an error; we ignore it.
./infra/mc.sh "scoreboard objectives add badge_total dummy \"Badges\"" || true

# Kanto-style badges (can be repurposed for custom gyms later).
./infra/mc.sh "scoreboard objectives add badge_boulder dummy \"Boulder\"" || true
./infra/mc.sh "scoreboard objectives add badge_cascade dummy \"Cascade\"" || true
./infra/mc.sh "scoreboard objectives add badge_thunder dummy \"Thunder\"" || true
./infra/mc.sh "scoreboard objectives add badge_rainbow dummy \"Rainbow\"" || true
./infra/mc.sh "scoreboard objectives add badge_soul dummy \"Soul\"" || true
./infra/mc.sh "scoreboard objectives add badge_marsh dummy \"Marsh\"" || true
./infra/mc.sh "scoreboard objectives add badge_volcano dummy \"Volcano\"" || true
./infra/mc.sh "scoreboard objectives add badge_earth dummy \"Earth\"" || true

echo "Progression initialized: objectives badge_total + badge_*"

