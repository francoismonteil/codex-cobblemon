I can reproduce what looks like the same issue on a Fabric 1.21.1 multiplayer server.

Environment:
- Minecraft 1.21.1
- Fabric Loader 0.18.4
- Fabric API 0.116.8+1.21.1
- Carry On 2.2.4.4
- Cobblemon 1.7.3+1.21.1
- Dedicated multiplayer server

Observed behavior:
- When this bug happens, every online player gets disconnected, not only the player who triggered it.
- I reproduced it multiple times on 2026-03-12 at 21:07, 21:50, 22:03, 22:05 and 22:07 (server local time, UTC+1).
- I now have a clearer trigger:
  - around 22:02, player A was being carried by player B, and when player B crouched, 3 players were disconnected
  - around 22:06, another player was carrying me, and when the carrier crouched, both of us were disconnected, but a third player in The End was not disconnected
- So the trigger appears to be: a player is carrying another player, then the carrier crouches.
- Based on these two reproductions, the disconnect does not look strictly global to the whole server. It seems to affect players in the same relevant world/session context, while a player in another dimension was unaffected in one repro.
- Server logs always show the same payload id:

```text
[22:03:11] [Netty Epoll Server IO #15/ERROR]: Error sending packet clientbound/minecraft:custom_payload
io.netty.handler.codec.EncoderException: Failed to encode packet 'clientbound/minecraft:custom_payload' (carryon:sync_carry_data)
Caused by: java.lang.NullPointerException
```

- Client logs show:

```text
[22:03:13] [Render thread/WARN]: Client disconnected with reason: Internal Exception: io.netty.handler.codec.EncoderException: Failed to encode packet 'clientbound/minecraft:custom_payload' (carryon:sync_carry_data)
```

- I also saw secondary server-side effects such as:
  - `Negative index in crash report handler`
  - `Failed to save player data for <player>`

What I can confirm:
- this is reproducible
- it happens in multiplayer
- it disconnects multiple players at once
- the failing payload is always `carryon:sync_carry_data`

What I cannot confirm yet:
- I have not reduced this to Carry On without Cobblemon
- I have not reduced this to a minimal mod set yet

So for now I can only report this as a Carry On <-> Cobblemon multiplayer compatibility issue, but the payload and disconnect behavior look very close to this issue.

If useful, I can follow up with:
- the exact in-game trigger once I write it down cleanly
- a smaller mod list
- the full client/server logs around one occurrence
