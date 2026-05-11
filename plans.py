from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict

from usage_meter import DB_PATH, init_usage_db


PLAN_LIMITS = {
    "free": 1000,
    "starter": 10000,
    "pro": 100000,
    "enterprise": None,
}


def current_month_key() -> str:
    now = datetime.now(timezone.utc)
    return f"{now.year:04d}-{now.month:02d}"


def get_active_plan() -> str:
    plan = os.getenv("AGENTTXGUARD_PLAN", "free").lower().strip()
    return plan if plan in PLAN_LIMITS else "free"


def monthly_usage_count() -> int:
    init_usage_db()
    month_key = current_month_key()

    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            """
            SELECT COUNT(*)
            FROM usage_events
            WHERE substr(timestamp_utc, 1, 7) = ?
            """,
            (month_key,),
        ).fetchone()

    return int(row[0] or 0)


def usage_policy_summary() -> Dict[str, Any]:
    plan = get_active_plan()
    limit = PLAN_LIMITS[plan]
    used = monthly_usage_count()

    if limit is None:
        remaining = None
        percent_used = None
        over_limit = False
    else:
        remaining = max(limit - used, 0)
        percent_used = round((used / limit) * 100, 2) if limit else None
        over_limit = used >= limit

    return {
        "plan": plan,
        "month": current_month_key(),
        "monthly_limit": limit,
        "used_this_month": used,
        "remaining_this_month": remaining,
        "percent_used": percent_used,
        "over_limit": over_limit,
        "available_plans": {
            "free": "1,000 calls/month",
            "starter": "10,000 calls/month",
            "pro": "100,000 calls/month",
            "enterprise": "custom/unlimited",
        },
    }
