# Metrics & Monitoring

## Overview

This adds two kinds of observability to the REST API:

* **Operational metrics (Prometheus):** requests/second, latencies, error rates, exposed at **`/metrics`** and scraped by Prometheus; visualized in Grafana.
* **Product usage (MySQL):** the middleware writes one row per “asset-shaped” request to **`asset_access_log`** so we can query **top assets** (popularity) and build dashboards. Returned via **`/stats/top/{resource_type}`**.

Low-coupling design: a small middleware observes the path and logs access; routers are unchanged. Path parsing is centralized to handle version prefixes.

---

## Components

* **apiserver** — FastAPI app exposing:

  * **`/metrics`** (Prometheus exposition via `prometheus_fastapi_instrumentator`)
  * **`/stats/top/{resource_type}`** (JSON; success hits only)
* **MySQL** — table `asset_access_log` stores per-request asset hits
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
    { "asset_id": "data_p7v02a70CbBGKk29T8przBjf", "hits": 42 },
    { "asset_id": "data_g8912mLHg8i2hsJblKu6G78i",   "hits": 17 }
  ]
  ```

  * Reports only successful requests (status code 200).
  * `resource_type` is something like `datasets`, `models`, etc.

---

## What gets logged (middleware)

“Asset-shaped” paths are logged after the response completes, i.e., any endpoint starting with e.g., `/datasets`, `/models`, including `/assets`. Access to other endpoints, such as `/metrics` or `/docs` do not get logged by the middleware. This also works if the API is deployed with a path prefix, and access is captured regardless of which version of the API is used (e.g., `/v2` or latest). The middleware does *not* log *who* accessed the log in any way (though the webserver itself does log incoming requests, these are not stored to the database).

---

## Table schema: `asset_access_log`

* `id` (PK)
* `asset_id` (string) — the identifier of the asset, e.g., `data_f8aa9...`.
* `resource_type` (string) — e.g. `datasets`, `models`, etc.
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
FROM asset_access_log
WHERE resource_type='datasets' AND status=200
GROUP BY asset
ORDER BY hits DESC
LIMIT 10;

-- All assets by type
SELECT resource_type AS type, asset_id AS asset, COUNT(*) AS hits
FROM asset_access_log
WHERE status=200
GROUP BY type, asset
ORDER BY hits DESC;

-- Top assets last 24h
SELECT resource_type AS type, asset_id AS asset, COUNT(*) AS hits
FROM asset_access_log
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
