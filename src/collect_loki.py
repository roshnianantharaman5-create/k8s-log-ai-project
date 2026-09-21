from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests


def query_loki(url: str, query: str, minutes: int = 30) -> list[dict]:
    end = datetime.now(timezone.utc)
    start = end - timedelta(minutes=minutes)
    response = requests.get(
        f"{url.rstrip('/')}/loki/api/v1/query_range",
        params={
            "query": query,
            "start": int(start.timestamp() * 1_000_000_000),
            "end": int(end.timestamp() * 1_000_000_000),
            "limit": 5000,
            "direction": "backward",
        },
        timeout=30,
    )
    response.raise_for_status()
    records: list[dict] = []
    for stream in response.json().get("data", {}).get("result", []):
        labels = stream.get("stream", {})
        for timestamp, line in stream.get("values", []):
            record = {**labels, "timestamp": timestamp}
            try:
                parsed = json.loads(line)
                if isinstance(parsed, dict):
                    record.update(parsed)
                else:
                    record["message"] = line
            except json.JSONDecodeError:
                record["message"] = line
            records.append(record)
    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--query", default='{namespace="ai-monitoring"}')
    parser.add_argument("--minutes", type=int, default=30)
    parser.add_argument("--output", default="data/raw/loki.jsonl")
    args = parser.parse_args()
    records = query_loki(args.url, args.query, args.minutes)
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record) + "\n")
    print(f"collected {len(records)} records to {path}")


if __name__ == "__main__":
    main()
