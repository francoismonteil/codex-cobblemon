# Places a pokecenter template and drops an origin marker so it can be cleared later.
#
# Usage:
#   execute positioned <x> <y> <z> run function acm:village/pokecenter/place_marked
#
# Then later:
#   function acm:village/pokecenter/clear_nearest

place template acm:village/pokecenter ~ ~ ~
summon minecraft:marker ~ ~ ~ {Tags:["acm.pokecenter_origin"]}

