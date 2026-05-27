from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
import yaml


@pytest.fixture()
def sample_gateway_config(tmp_path: Path) -> Path:
    data_dir = tmp_path / "orders"
    data_dir.mkdir()
    table = pa.table({
        "order_id": [1, 2, 3],
        "order_date": ["2026-01-01", "2026-01-02", "2026-01-03"],
        "region": ["US", "EU", "APAC"],
        "amount": [10.0, 20.0, 30.0],
        "margin": [1.0, 2.0, 3.0],
        "customer_email": ["a@example.com", "b@example.com", "c@example.com"],
    })
    pq.write_table(table, data_dir / "part-000.parquet")

    config = {
        "settings": {
            "data_root": str(tmp_path),
            "max_limit": 1000,
            "default_limit": 100,
            "query_timeout_seconds": 30,
        },
        "users": [
            {
                "id": "alice",
                "token": "analyst-token",
                "roles": ["analyst"],
                "attributes": {"regions": ["US", "EU"]},
            },
            {
                "id": "admin",
                "token": "admin-token",
                "roles": ["admin"],
                "attributes": {"regions": ["US", "EU", "APAC"]},
            },
        ],
        "datasets": {
            "orders": {
                "description": "Orders",
                "path": "orders/*.parquet",
                "roles": ["analyst", "admin"],
                "columns": {
                    "analyst": ["order_id", "order_date", "region", "amount"],
                    "admin": ["order_id", "order_date", "region", "amount", "margin", "customer_email"],
                },
                "row_policy": {
                    "field": "region",
                    "source": "attributes.regions",
                },
            }
        },
    }
    config_path = tmp_path / "gateway.yml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    return config_path
