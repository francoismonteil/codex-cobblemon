# Clears the pokecenter volume by setting it to air.
#
# Usage:
#   execute positioned <x> <y> <z> run function acm:village/pokecenter/clear_at
#
# Where <x> <y> <z> is the same origin you used for:
#   place template acm:village/pokecenter <x> <y> <z>

fill ~0 ~0 ~0 ~20 ~10 ~15 minecraft:air replace
