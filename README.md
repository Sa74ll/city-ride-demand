# 🚴‍♂️ City‑Ride Demand Predictor

![build](https://img.shields.io/github/actions/workflow/status/Sa74ll/city-ride-demand/ci.yml?label=build)  ![coverage](https://img.shields.io/codecov/c/github/Sa74ll/city-ride-demand?label=cov)  ![license](https://img.shields.io/github/license/Sa74ll/city-ride-demand)

> **Mission** — Predict, every minute, how many bikes *and* empty docks will be available at any Santander Cycles station **30 minutes into the future**, and serve the forecast via a public JSON API.

---

## 🌟 Why it matters

* **Riders** can decide whether to walk, scoot, or wait — no more arriving to an empty dock.
* **Operators** rebalance proactively, cutting redistribution mileage and CO₂.
* **Open‑data community** gets a reproducible real‑time ML reference app (Python ⇢ Cloud).

---

## 🔧 Tech Stack

| Phase ↴        | Dev tools                             | Cloud / Prod                   |
| -------------- | ------------------------------------- | ------------------------------ |
| Ingestion      | Python 3.12 · `aiohttp` · Docker cron | **AWS Lambda (cron → SQS)**    |
| Object store   | MinIO                                 | **S3**                         |
| Time‑series DB | Timescale (Docker)                    | **RDS + Timescale ext**        |
| Feature/ML     | pandas · XGBoost · MLflow · ONNX      | same, run on **GitHub Runner** |
| Serving API    | FastAPI · Uvicorn · `onnxruntime`     | **AWS Fargate**                |
| IaC            | Docker Compose (dev)                  | **Terraform**                  |
| Observability  | Prometheus · Loki logs                | **Grafana Cloud**              |

---

## 🗺️ Architecture (bird’s‑eye)

```text
          +----------------- TfL BikePoint (JSON every 60 s) -----------------+
          |                                                                  |
          v                                                                  |
+----------------+      raw snapshots     +----------------+                 |
|  Ingest Cron   |  ───────────────────→ |   S3 / MinIO    |                 |
|  (Docker)      |                       +-----------------+                 |
+-------┬--------+                                                   Weather |
        |  COPY                                         +-------------------+
        |                                               |
        v                                               |
+----------------+             +----------------+       |
| Timescale DB   |  features → |  ML trainer    |       |
|   hypertable   |   ONNX ←──  |  (MLflow)      |       |
+-------┬--------+             +--------┬-------+       |
        |                                 |              |
        | metrics (Prom)                  |              |
        v                                 v              |
+----------------+             +----------------+        |
|   FastAPI      |  ← predict  | Grafana / Loki |  ←─────+
|  on Fargate    |             +----------------+
+----------------+
```

*(Run `make viz` anytime to regenerate this diagram from `/docs/architecture.puml`.)*

---

## 🚀 Quick Start (local dev)

```bash
# 1) spin up infra
docker compose up -d timescaledb minio grafana

# 2) install deps & hooks
poetry install && pre-commit install

# 3) pull live data for one hour
poetry run python src/ingest/tfl_fetcher.py --minutes 60

# 4) train a baseline model
make train

# 5) start API and query a forecast
make api &  # (fastapi on :8000)

curl -X POST http://localhost:8000/predict \
     -H "Content-Type: application/json" \
     -d '{"station_id":"BikePoints_398","horizon":30}'
```

---

## 📅 Roadmap & Milestones

* **Kick‑off:** 18 Jun 2025
* **Current sprint:** Week 1 – raw snapshots to object storage
* 🗂 Follow progress on the **[Project board](../../projects)** (Kanban + Gantt).

---

## 🤝 Contributing

1. Fork ➜ Branch ➜ PR.
2. `make lint && make test` must pass.
3. One small feature per PR, please.

For full guidelines see [`/CONTRIBUTING.md`](/CONTRIBUTING.md).

![footer](https://raw.githubusercontent.com/Sa74ll/city-ride-demand/main/docs/assets/footer-bike.gif)
