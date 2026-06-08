scoreboard players set @s aca_portal 0
scoreboard players set @s aca_cd 100
execute in acm_academy:academy if entity @e[type=minecraft:marker,tag=acm_academy.arrival_academy,limit=1] run tp @s @e[type=minecraft:marker,tag=acm_academy.arrival_academy,limit=1,sort=nearest]
execute in acm_academy:academy unless entity @e[type=minecraft:marker,tag=acm_academy.arrival_academy,limit=1] run tp @s 0 91 4
title @s actionbar {"text":"Academy hub reached","color":"gold"}
