from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AuditEvent:
    user_id: str
    dataset: str | None
    action: str
    allowed: bool
    reason: str | None = None
    details: dict[str, Any] | None = None
    row_count: int | None = None
    duration_ms: int | None = None


class AuditLog:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        return sqlite3.connect(self.path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    dataset TEXT,
                    action TEXT NOT NULL,
                    allowed INTEGER NOT NULL,
                    reason TEXT,
                    details_json TEXT,
                    row_count INTEGER,
                    duration_ms INTEGER
                )
                """
            )

    def record(self, event: AuditEvent) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO audit_events (
                    ts, user_id, dataset, action, allowed, reason,
                    details_json, row_count, duration_ms
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.now(UTC).isoformat(),
                    event.user_id,
                    event.dataset,
                    event.action,
                    1 if event.allowed else 0,
                    event.reason,
                    json.dumps(event.details or {}, sort_keys=True),
                    event.row_count,
                    event.duration_ms,
                ),
            )

    def recent(self, limit: int = 100) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT ts, user_id, dataset, action, allowed, reason, details_json, row_count, duration_ms
                FROM audit_events
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            {
                "ts": row[0],
                "user_id": row[1],
                "dataset": row[2],
                "action": row[3],
                "allowed": bool(row[4]),
                "reason": row[5],
                "details": json.loads(row[6] or "{}"),
                "row_count": row[7],
                "duration_ms": row[8],
            }
            for row in rows
        ]
