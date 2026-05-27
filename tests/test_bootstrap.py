from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import yaml

from parquet_gateway.bootstrap import build_initial_config, discover_data_root, write_initial_config
from parquet_gateway.config import GatewayConfig


def write_parquet(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    table = pa.table({
        "order_id": [1],
        "region": ["US"],
        "amount": [10.0],
    })
    pq.write_table(table, path)


def test_discover_data_root_reads_parquet_and_extensionless_files(tmp_path: Path):
    write_parquet(tmp_path / "orders" / "part-000.parquet")
    extensionless = tmp_path / "events" / "000000_0_2026-04"
    extensionless.parent.mkdir()
    extensionless.write_bytes((tmp_path / "orders" / "part-000.parquet").read_bytes())
    (tmp_path / "notes").mkdir()
    (tmp_path / "notes" / "readme.txt").write_text("not parquet", encoding="utf-8")

    datasets = discover_data_root(tmp_path)

    assert datasets == [
        {
            "id": "events",
            "path": "events/*",
            "description": "events",
            "columns": ["order_id", "region", "amount"],
            "file_count": 1,
        },
        {
            "id": "orders",
            "path": "orders/*.parquet",
            "description": "orders",
            "columns": ["order_id", "region", "amount"],
            "file_count": 1,
        },
    ]


def test_build_initial_config_generates_valid_admin_and_analyst_config(tmp_path: Path):
    write_parquet(tmp_path / "orders" / "part-000.parquet")

    config, secrets = build_initial_config(
        data_root=tmp_path,
        admin_token="admin-secret",
        analyst_token="analyst-secret",
        gateway_token_secret="gateway-secret",
    )

    GatewayConfig.model_validate(config)
    assert secrets == {
        "admin_token": "admin-secret",
        "analyst_token": "analyst-secret",
        "gateway_token_secret": "gateway-secret",
    }
    assert config["settings"]["data_root"] == str(tmp_path)
    assert config["users"] == [
        {"id": "admin", "token": "admin-secret", "roles": ["admin"], "attributes": {}},
        {"id": "analyst", "token": "analyst-secret", "roles": ["analyst"], "attributes": {}},
    ]
    assert config["datasets"]["orders"] == {
        "description": "orders",
        "path": "orders/*.parquet",
        "roles": ["analyst", "admin"],
        "columns": {
            "analyst": ["order_id", "region", "amount"],
            "admin": ["order_id", "region", "amount"],
        },
    }


def test_write_initial_config_refuses_to_overwrite_without_flag(tmp_path: Path):
    write_parquet(tmp_path / "orders" / "part-000.parquet")
    output = tmp_path / "production.yml"
    output.write_text("existing: true\n", encoding="utf-8")

    try:
        write_initial_config(data_root=tmp_path, output_path=output, overwrite=False)
    except FileExistsError as exc:
        assert str(output) in str(exc)
    else:
        raise AssertionError("expected FileExistsError")

    assert yaml.safe_load(output.read_text(encoding="utf-8")) == {"existing": True}


def test_write_initial_config_writes_valid_yaml(tmp_path: Path):
    write_parquet(tmp_path / "orders" / "part-000.parquet")
    output = tmp_path / "production.yml"

    config, secrets = write_initial_config(
        data_root=tmp_path,
        output_path=output,
        admin_token="admin-secret",
        analyst_token="analyst-secret",
        gateway_token_secret="gateway-secret",
    )

    assert output.exists()
    assert yaml.safe_load(output.read_text(encoding="utf-8")) == config
    assert secrets["admin_token"] == "admin-secret"
