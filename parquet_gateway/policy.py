from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from parquet_gateway.auth import Principal
from parquet_gateway.config import DatasetConfig, GatewayConfig
from parquet_gateway.errors import NotFound, PermissionDenied


@dataclass(frozen=True)
class DatasetAccess:
    dataset_id: str
    dataset: DatasetConfig
    allowed_columns: frozenset[str]
    parquet_path: str


def resolve_dataset_access(config: GatewayConfig, principal: Principal, dataset_id: str) -> DatasetAccess:
    dataset = config.datasets.get(dataset_id)
    if dataset is None:
        raise NotFound(f"dataset {dataset_id!r} does not exist")
    if principal.roles.isdisjoint(dataset.roles):
        raise PermissionDenied(f"user {principal.id!r} cannot access dataset {dataset_id!r}")

    allowed: set[str] = set()
    for role in principal.roles:
        allowed.update(dataset.columns.get(role, []))
    if not allowed:
        raise PermissionDenied(f"user {principal.id!r} has no visible columns for dataset {dataset_id!r}")
    parquet_path = resolve_dataset_path(config, dataset)
    return DatasetAccess(
        dataset_id=dataset_id,
        dataset=dataset,
        allowed_columns=frozenset(allowed),
        parquet_path=parquet_path,
    )


def resolve_dataset_path(config: GatewayConfig, dataset: DatasetConfig) -> str:
    configured_path = Path(dataset.path)
    if configured_path.is_absolute():
        raise PermissionDenied("dataset paths must be relative to settings.data_root")
    if ".." in configured_path.parts:
        raise PermissionDenied("dataset paths cannot escape settings.data_root")
    data_root = Path(config.settings.data_root)
    return str(data_root / configured_path)


def list_visible_datasets(config: GatewayConfig, principal: Principal) -> list[dict[str, Any]]:
    visible = []
    for dataset_id, dataset in sorted(config.datasets.items()):
        if principal.roles.isdisjoint(dataset.roles):
            continue
        access = resolve_dataset_access(config, principal, dataset_id)
        visible.append({
            "id": dataset_id,
            "description": dataset.description,
            "columns": sorted(access.allowed_columns),
        })
    return visible


def resolve_attribute(principal: Principal, source: str) -> Any:
    parts = source.split(".")
    if not parts:
        raise PermissionDenied("row policy source is empty")
    current: Any
    if parts[0] == "attributes":
        current = principal.attributes
        parts = parts[1:]
    else:
        current = {"id": principal.id, "roles": sorted(principal.roles), "attributes": principal.attributes}
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            raise PermissionDenied(f"row policy source {source!r} is missing for user {principal.id!r}")
    return current
