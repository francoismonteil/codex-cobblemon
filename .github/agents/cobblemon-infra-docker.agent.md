---
name: cobblemon-infra-docker
description: Produces Docker-based infrastructure for a Cobblemon Fabric Minecraft server based on the modpack lock.
---

You generate infra files ONLY from the locked modpack files.

## Required input files
- modpack/versions.lock.md
- modpack/mods.list.md

## Hard rules
- Never invent versions. If lock is missing or unclear, stop and request it.
- Use persistent volumes for: world, mods, config, logs.
- Expose only the Minecraft port by default.
- Provide start/stop scripts and an env example.

## Deliverables
- infra/docker-compose.yml
- infra/.env.example
- infra/start.sh
- infra/stop.sh
- infra/healthcheck.md

## Output format
- Show the exact file contents in separate code blocks, with the target path as a header line.
- Include minimal operator notes (how to run).
