# Clears the nearest marked windmill (placed via acm:windmill/place_marked).
#
# Usage (ONE command):
#   function acm:windmill/clear_nearest

execute as @e[type=minecraft:marker,tag=acm.windmill_origin,sort=nearest,limit=1] at @s run function acm:windmill/clear
execute as @e[type=minecraft:marker,tag=acm.windmill_origin,sort=nearest,limit=1] run kill @s

