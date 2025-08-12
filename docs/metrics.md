# Metrics & Monitoring

## Overview

This adds two kinds of observability to the REST API:

* **Operational metrics (Prometheus):** requests/second, latencies, error rates, exposed at **`/metrics`** and scraped by Prometheus; visualized in Grafana.
* **Product usage (MySQL):** the middleware writes one row per “asset-shaped” request to **`assetaccesslog`** so we can query **top assets** (popularity) and build dashboards. Returned via **`/stats/top/{resource_type}`**.

Low-coupling design: a small middleware observes the path and logs access; routers are unchanged. Path parsing is centralized to handle version prefixes.

---

## Components

* **apiserver** — FastAPI app exposing:

  * **`/metrics`** (Prometheus exposition via `prometheus_fastapi_instrumentator`)
  * **`/stats/top/{resource_type}`** (JSON; success hits only)
* **MySQL** — table `assetaccesslog` stores per-request asset hits
* **Prometheus** — scrapes apiserver’s `/metrics`
* **Grafana** — visualizes Prometheus (traffic) + MySQL (popularity)

---

## Endpoints (apiserver)

* **GET `/metrics`**
  Exposes Prometheus metrics. Example series: `http_requests_total`, `http_request_duration_seconds`, process/python metrics, etc.

* **GET `/stats/top/{resource_type}?limit=10`**
  Returns an array of objects:

  ```json
  [
    { "asset_id": "v2/datasets/123", "hits": 42 },
    { "asset_id": "datasets/v1/1",   "hits": 17 }
  ]
  ```

  * Counts only **`status=200`** rows.
  * `resource_type` is something like `datasets`, `models`, etc.

---

## What gets logged (middleware)

“Asset-shaped” paths are logged after the response completes:

* **Logged (examples)**

  * `/datasets/abc`
  * `/datasets/v1/1`
  * `/v2/models/bert`
  * Optional deployment prefix is ignored: `/aiod-api/v10/datasets/xyz` → logs as `v10/datasets/xyz`

* **Excluded**

  * `/metrics`, `/docs`, `/openapi.json`, `/redoc`, `/favicon.ico`, `/counts`, `/health`, etc.

* **Privacy**

  * No user identifiers stored.

---

## Table schema: `assetaccesslog`

* `id` (PK)
* `asset_id` (string) — full tail of the asset path, with optional API version & resource type, e.g. `v2/datasets/123` or `datasets/v1/1`
* `resource_type` (string) — e.g. `datasets`, `models`, …
* `status` (int) — HTTP status code from the response
* `accessed_at` (UTC timestamp, indexed)

---

## Where the code lives

* Middleware: **`src/middleware/access_log.py`**
* Path parsing (version/deployment prefixes): **`src/middleware/path_parse.py`**
* Top-assets router: **`src/routers/access_stats_router.py`**
* Wiring (include router, add middleware, expose /metrics): **`src/main.py`**

---

## Run it

Start the API + monitoring stack (Prometheus, Grafana):

```bash
# helper
scripts/up.sh monitoring

# or directly
docker compose --env-file=.env --env-file=override.env \
  -f docker-compose.yaml -f docker-compose.dev.yaml \
  --profile monitoring up -d
```

Open:

* API Docs: `http://localhost:8000/docs`
* Metrics: `http://localhost:8000/metrics`
* Prometheus: `http://localhost:${PROMETHEUS_HOST_PORT:-9090}`
* Grafana: `http://localhost:${GRAFANA_HOST_PORT:-3000}`

Generate some traffic:

```bash
curl -s http://localhost:8000/datasets/abc        >/dev/null
curl -s http://localhost:8000/datasets/v1/1       >/dev/null
curl -s http://localhost:8000/v2/models/bert      >/dev/null
```

Check top assets (datasets):

```bash
curl -s "http://localhost:8000/stats/top/datasets?limit=5" | jq .
```

---

## Grafana: quick setup

Configure two data sources:

1. **Prometheus**

   * URL: `http://prometheus:9090`

2. **MySQL** (popularity)

   * Host: `sqlserver`
   * Port: `3306`
   * Database: `aiod`
   * User/password: from `.env`

**PromQL (traffic/latency examples):**

```promql
# Requests per endpoint (1m rate)
sum by (handler) (rate(http_requests_total[1m]))

# P95 latency by handler (5m window)
histogram_quantile(
  0.95,
  sum by (le, handler) (rate(http_request_duration_seconds_bucket[5m]))
)

# Error rate (4xx/5xx) per endpoint
sum by (handler) (rate(http_requests_total{status=~"4..|5.."}[5m]))
```

**MySQL (popularity examples):**

```sql
-- Top datasets (all time)
SELECT asset_id AS asset, COUNT(*) AS hits
FROM assetaccesslog
WHERE resource_type='datasets' AND status=200
GROUP BY asset
ORDER BY hits DESC
LIMIT 10;

-- All assets by type
SELECT resource_type AS type, asset_id AS asset, COUNT(*) AS hits
FROM assetaccesslog
WHERE status=200
GROUP BY type, asset
ORDER BY hits DESC;

-- Top assets last 24h
SELECT resource_type AS type, asset_id AS asset, COUNT(*) AS hits
FROM assetaccesslog
WHERE status=200 AND accessed_at >= NOW() - INTERVAL 1 DAY
GROUP BY type, asset
ORDER BY hits DESC
LIMIT 20;
```

(Optional) Provision defaults in repo:

```
grafana/provisioning/datasources/datasources.yml
grafana/provisioning/dashboards/dashboards.yml
grafana/provisioning/dashboards/aiod-metrics.json
```

---

## Tests

Focused middleware tests live under `src/tests/middleware/`:

```bash
PYTHONPATH=src pytest -q \
  src/tests/middleware/test_path_parse.py \
  src/tests/middleware/test_access_log_middleware.py
```

They cover:

* Path parsing of `/datasets/abc`, `/datasets/v1/1`, `/v2/models/bert`, etc.
* That asset hits are written for 200s and 404s.
* That excluded paths (e.g., `/metrics`) are ignored.

---

## Which service exposes `/stats`?

The **apiserver** (REST API) exposes `/stats/top/{resource_type}`. It’s mounted with the other routers in `src/main.py`.

---
