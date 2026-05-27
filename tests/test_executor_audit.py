from __future__ import annotations

from parquet_gateway.audit import AuditEvent, AuditLog
from parquet_gateway.auth import TokenAuthenticator
from parquet_gateway.config import load_config
from parquet_gateway.executor import DuckDBExecutor
from parquet_gateway.models import QueryRequest
from parquet_gateway.query_builder import compile_query


def test_executor_reads_parquet_with_row_policy(sample_gateway_config):
    config = load_config(sample_gateway_config)
    principal = TokenAuthenticator(config).authenticate_header("Bearer analyst-token")
    compiled = compile_query(config, principal, QueryRequest.model_validate({
        "dataset": "orders",
        "select": ["order_id", "region"],
        "order_by": [{"field": "order_id", "direction": "asc"}],
        "limit": 10,
    }))

    response = DuckDBExecutor(config).execute(compiled)

    assert response.row_count == 2
    assert response.rows == [
        {"order_id": 1, "region": "US"},
        {"order_id": 2, "region": "EU"},
    ]


def test_audit_records_events(tmp_path):
    audit = AuditLog(tmp_path / "audit.sqlite3")

    audit.record(AuditEvent(
        user_id="alice",
        dataset="orders",
        action="query",
        allowed=False,
        reason="denied",
    ))

    events = audit.recent()
    assert len(events) == 1
    assert events[0]["user_id"] == "alice"
    assert events[0]["allowed"] is False
    assert events[0]["reason"] == "denied"
