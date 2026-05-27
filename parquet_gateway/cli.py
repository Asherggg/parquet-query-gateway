from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Any, Protocol
from urllib import error, request


class JSONClient(Protocol):
    def request_json(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        ...


class GatewayHTTPClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip("/")
        self.token = token

    def request_json(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        req = request.Request(
            self.base_url + path,
            data=body,
            method=method,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
        )
        try:
            with request.urlopen(req, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8")
            raise SystemExit(f"gateway returned HTTP {exc.code}: {detail}") from exc


def main(argv: list[str] | None = None, client: JSONClient | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    actual_client = client or client_from_environment()

    if args.command == "datasets":
        output = actual_client.request_json("GET", "/datasets")
    elif args.command == "schema":
        output = actual_client.request_json("GET", f"/datasets/{args.dataset}/schema")
    elif args.command == "query":
        payload = build_query_payload(
            dataset=args.dataset,
            select=args.select,
            where=args.where,
            group_by=args.group_by,
            aggregate=args.aggregate,
            order_by=args.order_by,
            limit=args.limit,
        )
        output = actual_client.request_json("POST", "/query", payload)
    elif args.command == "audit":
        output = actual_client.request_json("GET", f"/admin/audit?limit={args.limit}")
    else:
        parser.error("unknown command")

    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="parquet-gw", description="CLI client for Parquet Query Gateway")
    subcommands = parser.add_subparsers(dest="command", required=True)

    subcommands.add_parser("datasets", help="List datasets visible to the current token")

    schema = subcommands.add_parser("schema", help="Show visible schema for a dataset")
    schema.add_argument("dataset")

    query = subcommands.add_parser("query", help="Run a permission-controlled query")
    query.add_argument("dataset")
    query.add_argument("--select", help="Comma-separated fields, e.g. order_id,amount")
    query.add_argument("--where", action="append", default=[], help="Filter, e.g. amount>=10 or region in [\"US\"]")
    query.add_argument("--group-by", help="Comma-separated grouping fields")
    query.add_argument("--aggregate", action="append", default=[], help="Aggregate, e.g. sum:amount:total_amount or count::rows")
    query.add_argument("--order-by", help="Sort expression, e.g. amount:desc")
    query.add_argument("--limit", type=int)

    audit = subcommands.add_parser("audit", help="Show recent audit events; requires admin role")
    audit.add_argument("--limit", type=int, default=100)
    return parser


def client_from_environment() -> GatewayHTTPClient:
    base_url = os.environ.get("PARQUET_GATEWAY_URL", "http://127.0.0.1:8080")
    token = os.environ.get("PARQUET_GATEWAY_TOKEN")
    if not token:
        raise SystemExit("PARQUET_GATEWAY_TOKEN is required")
    return GatewayHTTPClient(base_url, token)


def build_query_payload(
    *,
    dataset: str,
    select: str | None,
    where: list[str],
    group_by: str | None,
    aggregate: list[str],
    order_by: str | None,
    limit: int | None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"dataset": dataset}
    if select:
        payload["select"] = split_csv(select)
    if where:
        payload["filters"] = [parse_filter(expr) for expr in where]
    if group_by:
        payload["group_by"] = split_csv(group_by)
    if aggregate:
        payload["aggregates"] = [parse_aggregate(expr) for expr in aggregate]
    if order_by:
        field, direction = parse_order_by(order_by)
        payload["order_by"] = [{"field": field, "direction": direction}]
    if limit is not None:
        payload["limit"] = limit
    return payload


def split_csv(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


FILTER_PATTERN = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)(>=|<=|!=|=|>|<| contains | startswith | in )(.+)$")


def parse_filter(expr: str) -> dict[str, Any]:
    match = FILTER_PATTERN.match(expr.strip())
    if not match:
        raise SystemExit(f"invalid --where expression: {expr}")
    field, op, raw_value = match.groups()
    op = op.strip()
    return {"field": field, "op": op, "value": parse_value(raw_value.strip())}


def parse_value(raw: str) -> Any:
    if raw.startswith("["):
        return json.loads(raw)
    if (raw.startswith('"') and raw.endswith('"')) or (raw.startswith("'") and raw.endswith("'")):
        return raw[1:-1]
    if raw.lower() == "true":
        return True
    if raw.lower() == "false":
        return False
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        return raw


def parse_aggregate(expr: str) -> dict[str, Any]:
    parts = expr.split(":")
    if len(parts) != 3:
        raise SystemExit(f"invalid --aggregate expression: {expr}")
    func, field, alias = parts
    payload: dict[str, Any] = {"func": func, "as": alias}
    if field:
        payload["field"] = field
    return payload


def parse_order_by(expr: str) -> tuple[str, str]:
    parts = expr.split(":")
    if len(parts) == 1:
        return parts[0], "asc"
    if len(parts) == 2 and parts[1] in {"asc", "desc"}:
        return parts[0], parts[1]
    raise SystemExit(f"invalid --order-by expression: {expr}")


if __name__ == "__main__":
    sys.exit(main())
