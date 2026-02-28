from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

_PLAYER_ALLOWED = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_")


class PlayerActionRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=3, max_length=16)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if any(ch not in _PLAYER_ALLOWED for ch in value):
            raise ValueError("Player names must contain only letters, digits, or underscores")
        return value


class PlayerAddRequest(PlayerActionRequest):
    op: bool = False


class OnboardRequest(PlayerActionRequest):
    op: bool = False


class JobResponse(BaseModel):
    job_id: str
    status: Literal["queued", "running", "succeeded", "failed"]


class StatusResponse(BaseModel):
    container_exists: bool
    container_state: str
    health: str
    players_online: Optional[int]
    players_max: Optional[int]
    whitelist_count: int
    last_status_line: Optional[str]
    updated_at: str


class LogResponse(BaseModel):
    lines: list[str]


class WhitelistResponse(BaseModel):
    names: list[str]


class JobDetailsResponse(BaseModel):
    id: str
    action: str
    status: Literal["queued", "running", "succeeded", "failed"]
    started_at: Optional[str]
    finished_at: Optional[str]
    exit_code: Optional[int]
    stdout_tail: str
    stderr_tail: str


class JobListResponse(BaseModel):
    jobs: list[JobDetailsResponse]
