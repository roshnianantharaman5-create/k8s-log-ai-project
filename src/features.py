from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable

import pandas as pd


NUMERIC_COLUMNS = [
    "latency_ms",
    "restart_count",
    "error_rate",
    "cpu_pct",
    "memory_pct",
    "error_count_5m",
    "warning_count_5m",
]


def _number(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def records_to_frame(records: Iterable[dict[str, Any]]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for record in records:
        message = str(record.get("message") or record.get("line") or "")
        timestamp = record.get("timestamp") or record.get("ts")
        if not timestamp:
            timestamp = datetime.now(timezone.utc).isoformat()
        rows.append(
            {
                "timestamp": timestamp,
                "text": message,
                "severity": str(record.get("severity", "INFO")).upper(),
                "event_type": str(record.get("event_type", "normal")),
                "failure_label": int(bool(record.get("failure_label", 0))),
                "latency_ms": _number(record.get("latency_ms")),
                "restart_count": _number(record.get("restart_count")),
                "error_rate": _number(record.get("error_rate")),
                "cpu_pct": _number(record.get("cpu_pct")),
                "memory_pct": _number(record.get("memory_pct")),
                "error_count_5m": _number(record.get("error_count_5m")),
                "warning_count_5m": _number(record.get("warning_count_5m")),
            }
        )
    return pd.DataFrame(rows)
