from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
import requests
from fastapi import FastAPI, HTTPException
from prometheus_client import Counter, Gauge, make_asgi_app
from pydantic import BaseModel, Field
from scipy.sparse import hstack

from collect_loki import query_loki
from features import NUMERIC_COLUMNS, records_to_frame


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = Path(os.getenv("ARTIFACTS_DIR", ROOT / "artifacts"))
LOKI_URL = os.getenv("LOKI_URL", "http://localhost:3100")
LOKI_QUERY = os.getenv("LOKI_QUERY", '{namespace="ai-monitoring"}')
bundle = joblib.load(ARTIFACTS / "model.joblib")
metrics = json.loads((ARTIFACTS / "metrics.json").read_text(encoding="utf-8"))

prediction_count = Counter("log_ai_predictions_total", "Number of predictions", ["result"])
latest_probability = Gauge("log_ai_failure_probability", "Latest predicted failure probability")

app = FastAPI(title="Kubernetes Log AI Prediction API", version="0.1.0")
app.mount("/metrics", make_asgi_app())


class LogRecord(BaseModel):
    message: str = ""
    timestamp: str | int | None = None
    severity: str = "INFO"
    event_type: str = "normal"
    failure_label: int = 0
    latency_ms: float = 0
    restart_count: float = 0
    error_rate: float = 0
    cpu_pct: float = 0
    memory_pct: float = 0
    error_count_5m: float = 0
    warning_count_5m: float = 0


class PredictionRequest(BaseModel):
    records: list[LogRecord] = Field(min_length=1)


def predict_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    frame = records_to_frame(records)
    x_text = bundle["vectorizer"].transform(frame["text"])
    x_num = bundle["scaler"].transform(frame[NUMERIC_COLUMNS])
    features = hstack([x_text, x_num]).tocsr()
    probabilities = bundle["model"].predict_proba(features)[:, 1]
    probability = float(probabilities.mean())
    predicted_failure = probability >= 0.5
    result = "failure" if predicted_failure else "normal"
    prediction_count.labels(result=result).inc()
    latest_probability.set(probability)
    return {
        "predicted_failure": predicted_failure,
        "failure_probability": round(probability, 4),
        "risk_level": "critical" if probability >= 0.8 else "warning" if probability >= 0.5 else "normal",
        "records_analyzed": len(records),
        "top_events": frame["event_type"].value_counts().head(5).to_dict(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/model")
def model_info() -> dict[str, Any]:
    return metrics


@app.post("/predict")
def predict(request: PredictionRequest) -> dict[str, Any]:
    return predict_records([record.model_dump() for record in request.records])


@app.get("/predict/current")
def predict_current() -> dict[str, Any]:
    try:
        records = query_loki(LOKI_URL, LOKI_QUERY, minutes=15)
    except requests.RequestException as exc:
        raise HTTPException(status_code=503, detail=f"Loki unavailable: {exc}") from exc
    if not records:
        return {"status": "no_data", "message": "No recent logs found", "records_analyzed": 0}
    return predict_records(records)


@app.get("/recent")
def recent(limit: int = 50) -> list[dict[str, Any]]:
    try:
        return query_loki(LOKI_URL, LOKI_QUERY, minutes=15)[-limit:]
    except requests.RequestException as exc:
        raise HTTPException(status_code=503, detail=f"Loki unavailable: {exc}") from exc
