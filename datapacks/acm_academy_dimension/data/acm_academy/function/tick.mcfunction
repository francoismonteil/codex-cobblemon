scoreboard players remove @a[scores={aca_cd=1..}] aca_cd 1
tag @a remove acm_academy.portal_zone
tag @a remove acm_academy.portal_entry
tag @a remove acm_academy.portal_return
execute as @e[type=minecraft:marker,tag=acm_academy.portal_overworld] at @s run tag @a[distance=..1.2,scores={aca_cd=0}] add acm_academy.portal_zone
execute as @e[type=minecraft:marker,tag=acm_academy.portal_overworld] at @s run tag @a[distance=..1.2,scores={aca_cd=0}] add acm_academy.portal_entry
execute as @e[type=minecraft:marker,tag=acm_academy.portal_overworld] at @s run scoreboard players add @a[distance=..1.2,scores={aca_cd=0}] aca_portal 1
execute as @e[type=minecraft:marker,tag=acm_academy.portal_return_marker] at @s run tag @a[distance=..1.2,scores={aca_cd=0}] add acm_academy.portal_zone
execute as @e[type=minecraft:marker,tag=acm_academy.portal_return_marker] at @s run tag @a[distance=..1.2,scores={aca_cd=0}] add acm_academy.portal_return
execute as @e[type=minecraft:marker,tag=acm_academy.portal_return_marker] at @s run scoreboard players add @a[distance=..1.2,scores={aca_cd=0}] aca_portal 1
scoreboard players set @a[tag=!acm_academy.portal_zone] aca_portal 0
title @a[tag=acm_academy.portal_zone,scores={aca_portal=1..29}] actionbar [{"text":"Academy teleport in ","color":"gold"},{"score":{"name":"@s","objective":"aca_portal"},"color":"yellow"},{"text":"/30","color":"gold"}]
execute as @a[tag=acm_academy.portal_entry,scores={aca_portal=30..}] run function acm_academy:portal/enter_academy
execute as @a[tag=acm_academy.portal_return,scores={aca_portal=30..}] run function acm_academy:portal/return_overworld
execute as @e[type=minecraft:marker,tag=acm_academy.boundary_center] at @s run function acm_academy:portal/soft_border
