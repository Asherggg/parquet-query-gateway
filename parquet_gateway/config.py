from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator


class Settings(BaseModel):
    data_root: str = "/home/ai_ds/sd_data_center"
    max_limit: int = Field(default=1000, ge=1, le=100_000)
    default_limit: int = Field(default=100, ge=1)
    query_timeout_seconds: int = Field(default=30, ge=1, le=3600)


class UserConfig(BaseModel):
    id: str
    token: str
    roles: list[str] = Field(default_factory=list)
    attributes: dict[str, Any] = Field(default_factory=dict)

    @field_validator("roles")
    @classmethod
    def require_roles(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("user must have at least one role")
        return value


class RowPolicyConfig(BaseModel):
    field: str
    source: str


class DatasetConfig(BaseModel):
    description: str = ""
    path: str
    roles: list[str] = Field(default_factory=list)
    columns: dict[str, list[str]]
    row_policy: RowPolicyConfig | None = None

    @field_validator("roles")
    @classmethod
    def require_dataset_roles(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("dataset must allow at least one role")
        return value


class GatewayConfig(BaseModel):
    settings: Settings = Field(default_factory=Settings)
    users: list[UserConfig]
    datasets: dict[str, DatasetConfig]

    @field_validator("users")
    @classmethod
    def require_unique_user_tokens(cls, value: list[UserConfig]) -> list[UserConfig]:
        tokens = [user.token for user in value]
        if len(tokens) != len(set(tokens)):
            raise ValueError("user tokens must be unique")
        return value


def load_config(path: str | Path) -> GatewayConfig:
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}
    return GatewayConfig.model_validate(raw)
