# Metrics & Monitoring

* **/metrics** – Prometheus exposition created by prometheus_fastapi_instrumentator.
* **/stats/top/{resource_type}** – JSON list '[asset_id, hits]', success only.
* **AssetAccessLog** – table schema.
* Quickstart – 'docker compose --profile monitoring up -d'.
* Queries – PromQL for per-endpoint, MySQL for per-asset popularity.