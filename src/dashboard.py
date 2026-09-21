from __future__ import annotations

import os

import pandas as pd
import requests
import streamlit as st


API_URL = os.getenv("PREDICTION_API_URL", "http://localhost:8080")
st.set_page_config(page_title="Kubernetes Log AI", layout="wide")
st.title("AI-Based Kubernetes Failure Prediction")
st.caption("Live log analysis for the demo-2048 Kubernetes workload")

if st.button("Refresh"):
    st.rerun()

try:
    health = requests.get(f"{API_URL}/health", timeout=10)
    model = requests.get(f"{API_URL}/model", timeout=10).json()
    prediction = requests.get(f"{API_URL}/predict/current", timeout=30).json()
except requests.RequestException as exc:
    st.error(f"Prediction API unavailable: {exc}")
    st.stop()

if health.ok:
    st.success("Prediction API is healthy")

columns = st.columns(4)
columns[0].metric("Risk", str(prediction.get("risk_level", "unknown")).upper())
columns[1].metric("Failure probability", f"{prediction.get('failure_probability', 0):.1%}")
columns[2].metric("Records analyzed", prediction.get("records_analyzed", 0))
columns[3].metric("Model F1", f"{model.get('f1', 0):.3f}")

st.subheader("Current prediction")
st.json(prediction)

st.subheader("Training evaluation")
metric_frame = pd.DataFrame(
    [{key.title(): model.get(key, 0) for key in ["accuracy", "precision", "recall", "f1"]}]
)
st.dataframe(metric_frame, use_container_width=True, hide_index=True)

st.subheader("Recent Kubernetes logs")
try:
    recent = requests.get(f"{API_URL}/recent?limit=100", timeout=30).json()
    if isinstance(recent, list) and recent:
        st.dataframe(pd.DataFrame(recent), use_container_width=True, hide_index=True)
    else:
        st.info("No recent logs returned")
except requests.RequestException as exc:
    st.warning(f"Recent logs unavailable: {exc}")
