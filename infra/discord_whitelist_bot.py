#!/usr/bin/env python3
"""Discord bot to manage Minecraft whitelist using local infra scripts.

Commands (slash):
- /mc info
- /mc check pseudo:<name>
- /mc whitelist pseudo:<name>
- /mc starter pseudo:<name>
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence

import discord
from discord import app_commands


LOG = logging.getLogger("discord_whitelist_bot")
MC_NAME_RE = re.compile(r"^[A-Za-z0-9_]{3,16}$")
JOIN_LINE_RE = re.compile(r"]:\s+([A-Za-z0-9_]{3,16}) joined the game$")


def _parse_id_set(raw: str) -> set[int]:
    values: set[int] = set()
    for part in (raw or "").replace(";", ",").split(","):
        part = part.strip()
        if not part:
            continue
        try:
            values.add(int(part))
        except ValueError:
            LOG.warning("Ignoring invalid Discord ID in env: %r", part)
    return values


@dataclass(frozen=True)
class Config:
    repo_root: Path
    token: str
    guild_id: Optional[int]
    allowed_channel_ids: set[int]
    allowed_role_ids: set[int]
    command_timeout_sec: int
    starter_watch_enabled: bool
    starter_log_file: Path

    @classmethod
    def from_env(cls) -> "Config":
        repo_root = Path(__file__).resolve().parents[1]
        token = os.getenv("DISCORD_BOT_TOKEN", "").strip()
        if not token:
            raise SystemExit("DISCORD_BOT_TOKEN is required")

        guild_raw = os.getenv("DISCORD_BOT_GUILD_ID", "").strip()
        guild_id = None
        if guild_raw:
            try:
                guild_id = int(guild_raw)
            except ValueError as exc:
                raise SystemExit(f"Invalid DISCORD_BOT_GUILD_ID: {guild_raw}") from exc

        timeout_raw = os.getenv("DISCORD_BOT_COMMAND_TIMEOUT_SEC", "20").strip() or "20"
        try:
            timeout_sec = max(5, int(timeout_raw))
        except ValueError as exc:
            raise SystemExit(
                f"Invalid DISCORD_BOT_COMMAND_TIMEOUT_SEC: {timeout_raw}"
            ) from exc

        return cls(
            repo_root=repo_root,
            token=token,
            guild_id=guild_id,
            allowed_channel_ids=_parse_id_set(os.getenv("DISCORD_BOT_ALLOWED_CHANNEL_IDS", "")),
            allowed_role_ids=_parse_id_set(os.getenv("DISCORD_BOT_ALLOWED_ROLE_IDS", "")),
            command_timeout_sec=timeout_sec,
            starter_watch_enabled=os.getenv(
                "DISCORD_BOT_STARTER_WATCH_ENABLED", "true"
            ).strip().lower()
            not in {"0", "false", "no", "off"},
            starter_log_file=Path(
                os.getenv("CHATOPS_LOG_FILE", str(repo_root / "data/logs/latest.log"))
            ),
        )


class McBot(discord.Client):
    def __init__(self, cfg: Config) -> None:
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.cfg = cfg
        self.tree = app_commands.CommandTree(self)
        self.mc_group = app_commands.Group(
            name="mc", description="Commandes Minecraft (whitelist / infos)"
        )
        self.tree.add_command(self.mc_group)
        self._starter_watch_task: Optional[asyncio.Task[None]] = None
        self._register_commands()

    async def setup_hook(self) -> None:
        if self.cfg.guild_id:
            guild = discord.Object(id=self.cfg.guild_id)
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            LOG.info("Synced %d command(s) to guild %s", len(synced), self.cfg.guild_id)
        else:
            synced = await self.tree.sync()
            LOG.info("Synced %d global command(s)", len(synced))

        if self.cfg.starter_watch_enabled:
            self._starter_watch_task = asyncio.create_task(self._starter_watch_loop())
            LOG.info("Starter watch enabled (log=%s)", self.cfg.starter_log_file)

    async def close(self) -> None:
        if self._starter_watch_task is not None:
            self._starter_watch_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._starter_watch_task
        await super().close()

    def _register_commands(self) -> None:
        @self.mc_group.command(name="info", description="Infos de connexion et install client")
        async def mc_info(interaction: discord.Interaction) -> None:
            if not await self._authorize(interaction):
                return
            await interaction.response.defer(ephemeral=True, thinking=True)
            result = await self._run_script(["bash", "infra/friend-info.sh", "--markdown"])
            if result.returncode != 0:
                await interaction.followup.send(
                    f"Echec friend-info (rc={result.returncode})\n```text\n{_short(result.stderr)}\n```",
                    ephemeral=True,
                )
                return
            text = result.stdout.strip() or "(sortie vide)"
            await interaction.followup.send(_clip_discord(text), ephemeral=True)

        @self.mc_group.command(name="check", description="Verifier whitelist/op pour un pseudo")
        @app_commands.describe(pseudo="Pseudo Minecraft (3-16 chars)")
        async def mc_check(interaction: discord.Interaction, pseudo: str) -> None:
            if not await self._authorize(interaction):
                return
            pseudo = pseudo.strip()
            if not MC_NAME_RE.fullmatch(pseudo):
                await interaction.response.send_message(
                    "Pseudo invalide (attendu: 3-16 caracteres [A-Za-z0-9_]).",
                    ephemeral=True,
                )
                return
            await interaction.response.defer(ephemeral=True, thinking=True)
            status = await self._player_status(pseudo)
            if isinstance(status, str):
                await interaction.followup.send(status, ephemeral=True)
                return
            lines = [
                f"Pseudo: `{pseudo}`",
                f"Whitelist: {'yes' if status.get('whitelisted') else 'no'}",
                f"Op: {'yes' if status.get('op') else 'no'}",
            ]
            if status.get("op_level") is not None:
                lines.append(f"Op level: `{status['op_level']}`")
            await interaction.followup.send("\n".join(lines), ephemeral=True)

        @self.mc_group.command(name="whitelist", description="Ajouter un pseudo a la whitelist")
        @app_commands.describe(pseudo="Pseudo Minecraft (3-16 chars)")
        async def mc_whitelist(interaction: discord.Interaction, pseudo: str) -> None:
            if not await self._authorize(interaction):
                return
            pseudo = pseudo.strip()
            if not MC_NAME_RE.fullmatch(pseudo):
                await interaction.response.send_message(
                    "Pseudo invalide (attendu: 3-16 caracteres [A-Za-z0-9_]).",
                    ephemeral=True,
                )
                return

            await interaction.response.defer(ephemeral=True, thinking=True)

            status = await self._player_status(pseudo)
            if isinstance(status, str):
                await interaction.followup.send(status, ephemeral=True)
                return

            if status.get("whitelisted"):
                await interaction.followup.send(
                    f"`{pseudo}` est deja dans la whitelist.", ephemeral=True
                )
                return

            result = await self._run_script(["bash", "infra/onboard.sh", pseudo])
            if result.returncode != 0:
                await interaction.followup.send(
                    (
                        f"Echec onboarding `{pseudo}` (rc={result.returncode})\n"
                        f"```text\n{_short(result.stderr or result.stdout)}\n```"
                    ),
                    ephemeral=True,
                )
                return

            await interaction.followup.send(
                (
                    f"`{pseudo}` ajoute a la whitelist.\n"
                    "Le script d'onboarding a ete lance (welcome/info + starter kit si active).\n"
                    "Si le joueur etait offline, le starter est mis en attente et sera donne a sa premiere connexion."
                ),
                ephemeral=True,
            )

        @self.mc_group.command(
            name="starter",
            description="Donner (ou mettre en attente) le starter kit pour un pseudo",
        )
        @app_commands.describe(pseudo="Pseudo Minecraft (3-16 chars)")
        async def mc_starter(interaction: discord.Interaction, pseudo: str) -> None:
            if not await self._authorize(interaction):
                return
            pseudo = pseudo.strip()
            if not MC_NAME_RE.fullmatch(pseudo):
                await interaction.response.send_message(
                    "Pseudo invalide (attendu: 3-16 caracteres [A-Za-z0-9_]).",
                    ephemeral=True,
                )
                return

            await interaction.response.defer(ephemeral=True, thinking=True)
            result = await self._run_script(["bash", "infra/starter.sh", "--queue-if-offline", pseudo])
            if result.returncode != 0:
                await interaction.followup.send(
                    (
                        f"Echec starter `{pseudo}` (rc={result.returncode})\n"
                        f"```text\n{_short(result.stderr or result.stdout)}\n```"
                    ),
                    ephemeral=True,
                )
                return

            out = (result.stdout or "").strip()
            if f"starter_delivered={pseudo}" in out:
                msg = f"Starter donne immediatement a `{pseudo}` (joueur en ligne)."
            elif f"starter_pending_queued={pseudo}" in out:
                msg = (
                    f"Starter mis en attente pour `{pseudo}`.\n"
                    "Il sera distribue automatiquement a sa prochaine connexion."
                )
            elif f"starter_pending_exists={pseudo}" in out:
                msg = f"Starter deja en attente pour `{pseudo}`."
            else:
                msg = f"Commande starter executee pour `{pseudo}`.\n```text\n{_short(out)}\n```"

            await interaction.followup.send(msg, ephemeral=True)

    async def _authorize(self, interaction: discord.Interaction) -> bool:
        if interaction.guild is None:
            await interaction.response.send_message(
                "Commande disponible uniquement dans un serveur Discord.",
                ephemeral=True,
            )
            return False

        if self.cfg.guild_id and interaction.guild_id != self.cfg.guild_id:
            await interaction.response.send_message(
                "Ce bot n'est pas autorise dans ce serveur Discord.",
                ephemeral=True,
            )
            return False

        if self.cfg.allowed_channel_ids and (interaction.channel_id not in self.cfg.allowed_channel_ids):
            await interaction.response.send_message(
                "Commande non autorisee dans ce salon.",
                ephemeral=True,
            )
            return False

        if self.cfg.allowed_role_ids:
            user = interaction.user
            if not isinstance(user, discord.Member):
                await interaction.response.send_message(
                    "Impossible de verifier vos roles (reessayez depuis le serveur).",
                    ephemeral=True,
                )
                return False
            role_ids = {role.id for role in user.roles}
            if not (role_ids & self.cfg.allowed_role_ids):
                await interaction.response.send_message(
                    "Vous n'avez pas le role requis pour cette commande.",
                    ephemeral=True,
                )
                return False

        return True

    async def _player_status(self, pseudo: str) -> dict | str:
        result = await self._run_script(["bash", "infra/player-check.sh", "--json", pseudo])
        if result.returncode != 0:
            return (
                f"Echec player-check (rc={result.returncode})\n"
                f"```text\n{_short(result.stderr or result.stdout)}\n```"
            )
        try:
            return json.loads(result.stdout or "{}")
        except json.JSONDecodeError:
            return f"Sortie invalide de player-check:\n```text\n{_short(result.stdout)}\n```"

    async def _run_script(self, args: Sequence[str]) -> subprocess.CompletedProcess[str]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: _run_command(self.cfg, args))

    async def _starter_watch_loop(self) -> None:
        log_file = str(self.cfg.starter_log_file)
        while not self.is_closed():
            proc: Optional[asyncio.subprocess.Process] = None
            try:
                if not self.cfg.starter_log_file.exists():
                    LOG.warning("Starter watch log file missing: %s", log_file)
                    await asyncio.sleep(5)
                    continue

                proc = await asyncio.create_subprocess_exec(
                    "tail",
                    "-n",
                    "0",
                    "-F",
                    log_file,
                    cwd=str(self.cfg.repo_root),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT,
                )
                LOG.info("Starter watch tail started pid=%s", proc.pid)

                assert proc.stdout is not None
                while True:
                    line_b = await proc.stdout.readline()
                    if not line_b:
                        break
                    line = line_b.decode("utf-8", errors="replace").rstrip("\r\n")
                    match = JOIN_LINE_RE.search(line)
                    if not match:
                        continue

                    player = match.group(1)
                    LOG.info("Join detected for %s; draining starter queue", player)
                    res = await self._run_script(["bash", "infra/starter.sh", "--drain-pending", player])
                    if res.returncode != 0:
                        LOG.warning(
                            "starter drain rc=%s player=%s out=%s",
                            res.returncode,
                            player,
                            _short(res.stderr or res.stdout, 300),
                        )
                        continue

                    out = (res.stdout or "").strip()
                    if out and "starter_pending_absent=" not in out:
                        LOG.info("starter drain player=%s out=%s", player, _short(out, 300))

                rc = await proc.wait()
                LOG.warning("Starter watch tail exited rc=%s; retrying", rc)
                await asyncio.sleep(2)
            except asyncio.CancelledError:
                if proc is not None and proc.returncode is None:
                    proc.terminate()
                    with contextlib.suppress(Exception):
                        await asyncio.wait_for(proc.wait(), timeout=2)
                raise
            except FileNotFoundError:
                LOG.warning("tail command not found; starter watch disabled for this run")
                return
            except Exception:
                LOG.exception("Starter watch loop error; retry in 5s")
                if proc is not None and proc.returncode is None:
                    proc.kill()
                    with contextlib.suppress(Exception):
                        await proc.wait()
                await asyncio.sleep(5)


def _run_command(cfg: Config, args: Sequence[str]) -> subprocess.CompletedProcess[str]:
    LOG.info("Run command: %s", " ".join(args))
    env = os.environ.copy()
    try:
        return subprocess.run(
            list(args),
            cwd=str(cfg.repo_root),
            env=env,
            capture_output=True,
            text=True,
            timeout=cfg.command_timeout_sec,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = (exc.stderr or "") + f"\nTimed out after {cfg.command_timeout_sec}s"
        return subprocess.CompletedProcess(list(args), 124, stdout, stderr)


def _short(text: str, max_chars: int = 1500) -> str:
    text = (text or "").replace("\r", "")
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."


def _clip_discord(text: str, max_chars: int = 1900) -> str:
    text = (text or "").strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."


def main() -> None:
    logging.basicConfig(
        level=os.getenv("DISCORD_BOT_LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    cfg = Config.from_env()
    LOG.info(
        "Starting bot repo=%s guild_id=%s channels=%s roles=%s timeout=%ss",
        cfg.repo_root,
        cfg.guild_id,
        sorted(cfg.allowed_channel_ids),
        sorted(cfg.allowed_role_ids),
        cfg.command_timeout_sec,
    )
    bot = McBot(cfg)
    bot.run(cfg.token, log_handler=None)


if __name__ == "__main__":
    main()
