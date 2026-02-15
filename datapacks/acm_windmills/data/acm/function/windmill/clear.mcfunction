# Clears the windmill volume (35x41x35) by setting it to air.
#
# Usage (ONE command):
#   execute positioned <x> <y> <z> run function acm:windmill/clear
#
# Where <x> <y> <z> is the same origin you used for:
#   place template acm:windmill_template <x> <y> <z>
#   OR the position you used for:
#   place structure acm:windmill <x> <y> <z>
#
# Notes:
# - We split the /fill into 2 parts to stay under the 32768 block limit.
# - /place structure may rotate/mirror the template. To be robust, we clear all 4 quadrants around the origin.
# - We temporarily forceload the covered chunks to avoid "That position is not loaded".

forceload add ~-34 ~-34 ~34 ~34

# Quadrant (+X,+Z)
fill ~0 ~0 ~0 ~34 ~20 ~34 minecraft:air replace
fill ~0 ~21 ~0 ~34 ~40 ~34 minecraft:air replace

# Quadrant (-X,+Z)
fill ~-34 ~0 ~0 ~0 ~20 ~34 minecraft:air replace
fill ~-34 ~21 ~0 ~0 ~40 ~34 minecraft:air replace

# Quadrant (+X,-Z)
fill ~0 ~0 ~-34 ~34 ~20 ~0 minecraft:air replace
fill ~0 ~21 ~-34 ~34 ~40 ~0 minecraft:air replace

# Quadrant (-X,-Z)
fill ~-34 ~0 ~-34 ~0 ~20 ~0 minecraft:air replace
fill ~-34 ~21 ~-34 ~0 ~40 ~0 minecraft:air replace

forceload remove ~-34 ~-34 ~34 ~34
