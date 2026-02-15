# Places a windmill template and drops an origin marker so it can be cleared later.
#
# Usage:
#   execute positioned <x> <y> <z> run function acm:windmill/place_marked
#
# Then later:
#   function acm:windmill/clear_nearest

place template acm:windmill_template ~ ~ ~
summon minecraft:marker ~ ~ ~ {Tags:["acm.windmill_origin"]}

