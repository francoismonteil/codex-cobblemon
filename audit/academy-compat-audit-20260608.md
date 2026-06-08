# Academy Compatibility Audit

- Generated at: `2026-06-08T13:42:15.381082+00:00`
- Base Cobblemon: `1.7.3+1.21.1`
- Upstream Academy Cobblemon: `1.6.1+1.21.1`
- Decision: `fidelity_reduced`
- Reason: Upstream StarAcademyMod currently pins Cobblemon 1.6.1+1.21.1, so the real Academy Integration path is blocked on the current Cobblemon 1.7.3 base unless upstream compatibility changes.

## Status Summary
- `blocked_without_fork`: academy-integration, academy-safari, academy-houses
- `viable_as_is`: ftb-library, ftb-teams, ftb-essentials, ftb-quests, numismatic-overhaul, extraquests
- `viable_with_simple_config`: rct-api, admiral, rad-gyms, eternal-starlight

## Install Groups
- `core`: ftb-library, ftb-teams, ftb-essentials, ftb-quests, numismatic-overhaul, extraquests
- `gyms`: rct-api, admiral, rad-gyms
- `dimension`: eternal-starlight

## Blocked Components
- `academy-integration`: Do not introduce a durable private fork just to bridge the Cobblemon API gap.
- `academy-safari`: The real Safari portal, timer and ticket systems are implemented inside StarAcademyMod.
- `academy-houses`: Acceptance letters, membership, house Pokedex and related GUI blocks are part of StarAcademyMod.
