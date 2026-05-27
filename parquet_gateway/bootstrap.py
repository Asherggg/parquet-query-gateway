from __future__ import annotations

import secrets
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq
import yaml

from parquet_gateway.config import GatewayConfig


def discover_data_root(data_root: str | Path) -> list[dict[str, Any]]:
    root = Path(data_root)
    if not root.exists():
        raise FileNotFoundError(f"data root does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"data root is not a directory: {root}")

    datasets: list[dict[str, Any]] = []
    for child in sorted((path for path in root.iterdir() if path.is_dir()), key=lambda path: path.name):
        parquet_files = [path for path in sorted(child.iterdir()) if path.is_file() and not path.name.startswith(".")]
        schema = None
        schema_file: Path | None = None
        for parquet_file in parquet_files:
            try:
                schema = pq.read_schema(parquet_file)
                schema_file = parquet_file
                break
            except Exception:
                continue
        if schema is None:
            continue
        datasets.append({
            "id": child.name,
            "path": f"{child.name}/*.parquet" if schema_file and schema_file.suffix == ".parquet" else f"{child.name}/*",
            "description": child.name,
            "columns": [field.name for field in schema],
            "file_count": len(parquet_files),
        })
    return datasets


def build_initial_config(
    *,
    data_root: str | Path,
    admin_token: str | None = None,
    analyst_token: str | None = None,
    gateway_token_secret: str | None = None,
    max_limit: int = 1000,
    default_limit: int = 100,
    query_timeout_seconds: int = 30,
) -> tuple[dict[str, Any], dict[str, str]]:
    datasets = discover_data_root(data_root)
    if not datasets:
        raise ValueError(f"no readable parquet datasets found under {Path(data_root)}")

    actual_admin_token = admin_token or make_token("pgw-admin")
    actual_analyst_token = analyst_token or make_token("pgw-analyst")
    actual_gateway_secret = gateway_token_secret or secrets.token_urlsafe(48)

    config: dict[str, Any] = {
        "settings": {
            "data_root": str(Path(data_root)),
            "max_limit": max_limit,
            "default_limit": default_limit,
            "query_timeout_seconds": query_timeout_seconds,
        },
        "users": [
            {"id": "admin", "token": actual_admin_token, "roles": ["admin"], "attributes": {}},
            {"id": "analyst", "token": actual_analyst_token, "roles": ["analyst"], "attributes": {}},
        ],
        "datasets": {},
        "auth": {
            "gateway_token_secret": actual_gateway_secret,
            "token_ttl_seconds": 28800,
            "feishu": {
                "enabled": False,
                "app_id": "",
                "app_secret": "",
                "redirect_uri": "http://127.0.0.1:8765/callback",
            },
            "feishu_users": [],
        },
    }

    for dataset in datasets:
        columns = list(dataset["columns"])
        config["datasets"][dataset["id"]] = {
            "description": dataset["description"],
            "path": dataset["path"],
            "roles": ["analyst", "admin"],
            "columns": {
                "analyst": columns,
                "admin": columns,
            },
        }

    GatewayConfig.model_validate(config)
    return config, {
        "admin_token": actual_admin_token,
        "analyst_token": actual_analyst_token,
        "gateway_token_secret": actual_gateway_secret,
    }


def write_initial_config(
    *,
    data_root: str | Path,
    output_path: str | Path,
    overwrite: bool = False,
    admin_token: str | None = None,
    analyst_token: str | None = None,
    gateway_token_secret: str | None = None,
) -> tuple[dict[str, Any], dict[str, str]]:
    output = Path(output_path)
    if output.exists() and not overwrite:
        raise FileExistsError(f"config already exists: {output}")

    config, generated = build_initial_config(
        data_root=data_root,
        admin_token=admin_token,
        analyst_token=analyst_token,
        gateway_token_secret=gateway_token_secret,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return config, generated


def make_token(prefix: str) -> str:
    return f"{prefix}-{secrets.token_urlsafe(32)}"
