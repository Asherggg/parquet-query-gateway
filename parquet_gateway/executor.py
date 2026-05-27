from __future__ import annotations

import time
from threading import Timer
from typing import Any

import duckdb

from parquet_gateway.config import GatewayConfig
from parquet_gateway.models import QueryResponse
from parquet_gateway.query_builder import CompiledQuery


class DuckDBExecutor:
    def __init__(self, config: GatewayConfig):
        self.config = config

    def execute(self, compiled: CompiledQuery) -> QueryResponse:
        start = time.perf_counter()
        with duckdb.connect(database=":memory:", read_only=False) as conn:
            conn.execute(f"SET threads = 4")
            timer = Timer(self.config.settings.query_timeout_seconds, conn.interrupt)
            timer.start()
            try:
                result = conn.execute(compiled.sql, compiled.params)
                names = [description[0] for description in result.description or []]
                rows = [row_to_dict(names, row) for row in result.fetchall()]
            finally:
                timer.cancel()
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return QueryResponse(
            rows=rows,
            row_count=len(rows),
            columns=names,
            query_ms=elapsed_ms,
            dataset=compiled.dataset_id,
        )


def row_to_dict(names: list[str], row: tuple[Any, ...]) -> dict[str, Any]:
    return {name: normalize_value(value) for name, value in zip(names, row, strict=True)}


def normalize_value(value: Any) -> Any:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value
