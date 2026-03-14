# [Bug] Fabric 1.21.1: client gets kicked on `carryon:sync_carry_data` custom payload

## Describe the bug

On a Fabric 1.21.1 dedicated multiplayer server, Carry On can disconnect one or more online players with:

`Internal Exception: io.netty.handler.codec.EncoderException: Failed to encode packet 'clientbound/minecraft:custom_payload' (carryon:sync_carry_data)`

The server logs show the same payload id every time and a `NullPointerException` during packet encoding.

At the moment I can confirm the behavior in a Cobblemon-based modpack, so I am reporting this conservatively as a Carry On <-> Cobblemon multiplayer compatibility issue, not yet as a pure Carry On vanilla/Fabric issue.

## To Reproduce

1. Start a Fabric 1.21.1 dedicated server with Carry On 2.2.4.4.
2. Join with multiple players.
3. Have one player carry another player with Carry On.
4. Make the carrier crouch while still carrying the other player.
5. Observe that the carried player and the carrier are disconnected immediately.
6. In some reproductions, additional nearby/same-context players are also disconnected.

## Expected behavior

Carry On should sync the carried state correctly and keep players connected.

## Actual behavior

Players are kicked with:

```text
Internal Exception: io.netty.handler.codec.EncoderException: Failed to encode packet 'clientbound/minecraft:custom_payload' (carryon:sync_carry_data)
```

## Screenshots

- attach the disconnected screen screenshot

## Game Information

- Minecraft: `1.21.1`
- Fabric Loader: `0.18.4`
- Fabric API: `0.116.8+1.21.1`
- Carry On: `2.2.4.4`
- Cobblemon: `1.7.3+1.21.1`

## Additional context

Client log:

```text
[22:03:13] [Render thread/WARN]: Client disconnected with reason: Internal Exception: io.netty.handler.codec.EncoderException: Failed to encode packet 'clientbound/minecraft:custom_payload' (carryon:sync_carry_data)
```

Server log:

```text
[22:03:11] [Netty Epoll Server IO #15/ERROR]: Error sending packet clientbound/minecraft:custom_payload
io.netty.handler.codec.EncoderException: Failed to encode packet 'clientbound/minecraft:custom_payload' (carryon:sync_carry_data)
Caused by: java.lang.NullPointerException
```

Other notes:
- I reproduced this multiple times on the same day
- in at least one occurrence, multiple online players were disconnected at once
- example repro details:
  - around `22:02`, I was being carried by another player, they crouched, and 3 players were disconnected
  - around `22:06`, another player was carrying me, they crouched, and both of us were disconnected while a third player in The End was unaffected
- I also saw `Negative index in crash report handler` and `Failed to save player data for <player>` after the disconnects
- before opening this as a new issue, check whether `https://github.com/Tschipp/CarryOn/issues/926` already covers the same root problem
