scoreboard players set @s aca_portal 0
scoreboard players set @s aca_cd 100
execute in minecraft:overworld if entity @e[type=minecraft:marker,tag=acm_academy.arrival_overworld,limit=1] run tp @s @e[type=minecraft:marker,tag=acm_academy.arrival_overworld,limit=1,sort=nearest]
execute in minecraft:overworld unless entity @e[type=minecraft:marker,tag=acm_academy.arrival_overworld,limit=1] run tp @s 24 90 0
title @s actionbar {"text":"Returned to legacy world","color":"green"}
