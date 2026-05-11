from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


DB_PATH = Path("agenttxguard_usage.sqlite3")


def init_usage_db() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS usage_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp_utc TEXT NOT NULL,
                endpoint TEXT NOT NULL,
                api_key_label TEXT,
                decision TEXT,
                safety_score REAL,
                agent_id TEXT,
                metadata_json TEXT
            )
            """
        )
        conn.commit()


def log_usage_event(
    endpoint: str,
    result: Dict[str, Any],
    api_key_label: Optional[str] = None,
) -> None:
    init_usage_db()

    metadata = result.get("metadata") or {}
    agent_id = metadata.get("agent_id")
    decision = result.get("decision")
    safety_score = result.get("safety_score")

    import json

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO usage_events (
                timestamp_utc,
                endpoint,
                api_key_label,
                decision,
                safety_score,
                agent_id,
                metadata_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                endpoint,
                api_key_label,
                decision,
                safety_score,
                agent_id,
                json.dumps(metadata, sort_keys=True),
            ),
        )
        conn.commit()


def usage_summary() -> Dict[str, Any]:
    init_usage_db()

    with sqlite3.connect(DB_PATH) as conn:
        total = conn.execute("SELECT COUNT(*) FROM usage_events").fetchone()[0]

        by_endpoint_rows = conn.execute(
            """
            SELECT endpoint, COUNT(*)
            FROM usage_events
            GROUP BY endpoint
            ORDER BY COUNT(*) DESC
            """
        ).fetchall()

        by_decision_rows = conn.execute(
            """
            SELECT decision, COUNT(*)
            FROM usage_events
            GROUP BY decision
            ORDER BY COUNT(*) DESC
            """
        ).fetchall()

        latest_rows = conn.execute(
            """
            SELECT timestamp_utc, endpoint, decision, safety_score, agent_id
            FROM usage_events
            ORDER BY id DESC
            LIMIT 10
            """
        ).fetchall()

    return {
        "total_events": total,
        "by_endpoint": [
            {"endpoint": row[0], "count": row[1]} for row in by_endpoint_rows
        ],
        "by_decision": [
            {"decision": row[0], "count": row[1]} for row in by_decision_rows
        ],
        "latest": [
            {
                "timestamp_utc": row[0],
                "endpoint": row[1],
                "decision": row[2],
                "safety_score": row[3],
                "agent_id": row[4],
            }
            for row in latest_rows
        ],
    }
