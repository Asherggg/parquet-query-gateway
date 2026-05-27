from __future__ import annotations

import json

from parquet_gateway.cli import build_query_payload, main


class FakeHTTPClient:
    def __init__(self):
        self.calls = []

    def request_json(self, method, path, payload=None):
        self.calls.append((method, path, payload))
        if path == "/datasets":
            return {"datasets": [{"id": "orders", "description": "Orders"}]}
        if path == "/datasets/orders/schema":
            return {"dataset": "orders", "columns": ["order_id", "amount"]}
        if path == "/query":
            return {"rows": [{"order_id": 1, "amount": 10.0}], "row_count": 1}
        if path == "/admin/audit?limit=25":
            return {"events": [{"user_id": "alice", "allowed": True}]}
        raise AssertionError(path)


def test_build_query_payload_from_cli_options():
    payload = build_query_payload(
        dataset="orders",
        select="order_id,amount",
        where=['amount>=10', 'region in ["US","EU"]'],
        group_by=None,
        aggregate=[],
        order_by="amount:desc",
        limit=5,
    )

    assert payload == {
        "dataset": "orders",
        "select": ["order_id", "amount"],
        "filters": [
            {"field": "amount", "op": ">=", "value": 10},
            {"field": "region", "op": "in", "value": ["US", "EU"]},
        ],
        "order_by": [{"field": "amount", "direction": "desc"}],
        "limit": 5,
    }


def test_cli_lists_datasets(capsys):
    client = FakeHTTPClient()

    code = main(["datasets"], client=client)

    assert code == 0
    assert client.calls == [("GET", "/datasets", None)]
    assert json.loads(capsys.readouterr().out)["datasets"][0]["id"] == "orders"


def test_cli_queries_dataset(capsys):
    client = FakeHTTPClient()

    code = main([
        "query",
        "orders",
        "--select",
        "order_id,amount",
        "--where",
        "amount>=10",
        "--limit",
        "5",
    ], client=client)

    assert code == 0
    method, path, payload = client.calls[0]
    assert method == "POST"
    assert path == "/query"
    assert payload["dataset"] == "orders"
    assert payload["select"] == ["order_id", "amount"]
    assert json.loads(capsys.readouterr().out)["row_count"] == 1


def test_cli_reads_audit_events(capsys):
    client = FakeHTTPClient()

    code = main(["audit", "--limit", "25"], client=client)

    assert code == 0
    assert client.calls == [("GET", "/admin/audit?limit=25", None)]
    assert json.loads(capsys.readouterr().out)["events"][0]["user_id"] == "alice"
