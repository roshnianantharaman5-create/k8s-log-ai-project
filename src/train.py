from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
from scipy.sparse import hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from features import NUMERIC_COLUMNS, records_to_frame
from synthetic import generate_records, write_jsonl


def load_records(path: Path) -> list[dict]:
    if not path.exists():
        records = generate_records(1600)
        write_jsonl(records, path)
        return records
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/raw/synthetic.jsonl")
    parser.add_argument("--artifacts", default="artifacts")
    args = parser.parse_args()
    artifact_dir = Path(args.artifacts)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    frame = records_to_frame(load_records(Path(args.input)))
    if frame["failure_label"].nunique() < 2:
        raise RuntimeError("training data must contain both normal and failure labels")
    train, test = train_test_split(frame, test_size=0.25, random_state=42, stratify=frame["failure_label"])
    vectorizer = TfidfVectorizer(max_features=2000, ngram_range=(1, 2), lowercase=True)
    scaler = StandardScaler()
    x_text_train = vectorizer.fit_transform(train["text"])
    x_text_test = vectorizer.transform(test["text"])
    x_num_train = scaler.fit_transform(train[NUMERIC_COLUMNS])
    x_num_test = scaler.transform(test[NUMERIC_COLUMNS])
    x_train = hstack([x_text_train, x_num_train]).tocsr()
    x_test = hstack([x_text_test, x_num_test]).tocsr()
    model = LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)
    model.fit(x_train, train["failure_label"])
    predictions = model.predict(x_test)
    probabilities = model.predict_proba(x_test)[:, 1]
    metrics = {
        "samples": int(len(frame)),
        "failure_rate": float(frame["failure_label"].mean()),
        "accuracy": float(accuracy_score(test["failure_label"], predictions)),
        "precision": float(precision_score(test["failure_label"], predictions, zero_division=0)),
        "recall": float(recall_score(test["failure_label"], predictions, zero_division=0)),
        "f1": float(f1_score(test["failure_label"], predictions, zero_division=0)),
        "confusion_matrix": confusion_matrix(test["failure_label"], predictions).tolist(),
        "classification_report": classification_report(test["failure_label"], predictions, output_dict=True, zero_division=0),
        "probability_mean": float(np.mean(probabilities)),
    }
    joblib.dump(
        {"vectorizer": vectorizer, "scaler": scaler, "model": model, "numeric_columns": NUMERIC_COLUMNS},
        artifact_dir / "model.joblib",
    )
    (artifact_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (artifact_dir / "feature_schema.json").write_text(json.dumps({"numeric_columns": NUMERIC_COLUMNS}, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
