# AI-Based Kubernetes Log Analysis

This project collects Kubernetes logs through the local Grafana LGTM stack, classifies normal and abnormal log windows, predicts likely failures, and exposes results through FastAPI and Streamlit.

## Local training

```powershell
python -m pip install -r requirements.txt
python src/train.py
```

## Collect logs from Loki

```powershell
python src/collect_loki.py --url http://localhost:3100 --output data/raw/loki.jsonl
```

## Build and deploy to kind

```powershell
python src/train.py
docker build -t k8s-log-ai:0.1.0 .
kind load docker-image k8s-log-ai:0.1.0 --name cloud2007
kubectl apply -f k8s/ai-monitoring.yaml
```

Endpoints:

- `http://ai-monitoring.localhost/health`
- `http://dashboard.localhost`
- `http://game-2048.localhost`
- `http://project.localhost` — presentation-style project walkthrough

## Deploy the project walkthrough

```powershell
docker build -t project-presentation:0.1.0 presentation
C:\Users\roshn\bin\kind.exe load docker-image project-presentation:0.1.0 --name cloud2007
kubectl apply -f k8s/presentation.yaml
```
