from __future__ import annotations

import argparse
import json
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


NORMAL_MESSAGES = [
    "request completed successfully",
    "health check passed",
    "cache lookup completed",
    "served game asset",
]

FAILURE_EVENTS = [
    ("http_error", "upstream request failed with HTTP 503", "ERROR"),
    ("timeout", "dependency request timed out after 5000ms", "ERROR"),
    ("crash_loop", "container restart detected after application crash", "CRITICAL"),
    ("memory_pressure", "memory usage exceeded safe operating limit", "WARNING"),
    ("latency_spike", "request latency exceeded failure threshold", "WARNING"),
]


def make_record(rng: random.Random, failure: bool | None = None) -> dict:
    failure = rng.random() < 0.35 if failure is None else failure
    now = datetime.now(timezone.utc).isoformat()
    if failure:
        event_type, message, severity = rng.choice(FAILURE_EVENTS)
        latency = rng.randint(900, 6000)
        restart = rng.randint(1, 5) if event_type == "crash_loop" else 0
        error_rate = round(rng.uniform(0.25, 0.95), 3)
        cpu = round(rng.uniform(70, 99), 2)
        memory = round(rng.uniform(75, 99), 2)
        errors = rng.randint(4, 40)
        warnings = rng.randint(2, 20)
    else:
        event_type = "normal"
        message = rng.choice(NORMAL_MESSAGES)
        severity = "INFO"
        latency = rng.randint(20, 220)
        restart = 0
        error_rate = round(rng.uniform(0, 0.04), 3)
        cpu = round(rng.uniform(5, 55), 2)
        memory = round(rng.uniform(15, 65), 2)
        errors = rng.randint(0, 1)
        warnings = rng.randint(0, 2)
    return {
        "timestamp": now,
        "namespace": "ai-monitoring",
        "pod": "log-generator",
        "service": "demo-2048",
        "severity": severity,
        "event_type": event_type,
        "message": message,
        "latency_ms": latency,
        "restart_count": restart,
        "error_rate": error_rate,
        "cpu_pct": cpu,
        "memory_pct": memory,
        "error_count_5m": errors,
        "warning_count_5m": warnings,
        "failure_label": int(failure),
    }


def generate_records(count: int, seed: int = 42) -> list[dict]:
    rng = random.Random(seed)
    return [make_record(rng) for _ in range(count)]


def write_jsonl(records: list[dict], output: str | Path) -> None:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=1000)
    parser.add_argument("--output", default="data/raw/synthetic.jsonl")
    parser.add_argument("--stream", action="store_true")
    parser.add_argument("--interval", type=float, default=2.0)
    args = parser.parse_args()
    rng = random.Random()
    if args.stream:
        while True:
            print(json.dumps(make_record(rng)), flush=True)
            time.sleep(args.interval)
    else:
        write_jsonl(generate_records(args.count), args.output)
        print(f"wrote {args.count} records to {args.output}")


if __name__ == "__main__":
    main()
