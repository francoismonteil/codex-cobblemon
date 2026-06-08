# Academy V2

This directory is the source of truth for the Academy rollout on top of the current
Cobblemon 1.7.3 base.

Current operating mode:

- `compatibility_gate.mode = fidelity_reduced`
- reason: the upstream `StarAcademyMod` repository still pins `Cobblemon 1.6.1+1.21.1`
- consequence: install the compatible Academy-adjacent stack now, but do not claim
  that the real Academy Safari / houses / acceptance-letter systems are available

Primary files:

- `stack.lock.json`: machine-readable compatibility matrix and pinned artifacts

Operator flow:

1. `./infra/academy-compat-audit.py`
2. `./infra/academy-stack-install.sh --all`
3. `./infra/install-academy-dimension-datapack.sh --restart`
4. `./infra/spawn-academy-portals.sh`
5. Follow `runbooks/academy-dimension.md`
