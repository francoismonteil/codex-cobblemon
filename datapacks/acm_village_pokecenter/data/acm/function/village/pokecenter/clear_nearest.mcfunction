# Clears the nearest marked pokecenter (placed via acm:village/pokecenter/place_marked).
#
# Usage (ONE command):
#   function acm:village/pokecenter/clear_nearest

execute as @e[type=minecraft:marker,tag=acm.pokecenter_origin,sort=nearest,limit=1] at @s run function acm:village/pokecenter/clear_at
execute as @e[type=minecraft:marker,tag=acm.pokecenter_origin,sort=nearest,limit=1] run kill @s

