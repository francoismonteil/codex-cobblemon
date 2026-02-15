# Clears the windmill volume (35x41x35) by setting it to air.
#
# Usage (ONE command):
#   execute positioned <x> <y> <z> run function acm:windmill/clear
#
# Where <x> <y> <z> is the same origin you used for:
#   place template acm:windmill_template <x> <y> <z>
#
# Notes:
# - We split the /fill into 2 parts to stay under the 32768 block limit.
# - We temporarily forceload the covered chunks to avoid "That position is not loaded".

forceload add ~ ~ ~34 ~34

fill ~0 ~0 ~0 ~34 ~20 ~34 minecraft:air replace
fill ~0 ~21 ~0 ~34 ~40 ~34 minecraft:air replace

forceload remove ~ ~ ~34 ~34

