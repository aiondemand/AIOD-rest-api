from fastapi import APIRouter
from sqlalchemy import func
from sqlmodel import select
from database.session import DbSession
from database.model.access.access_log import AssetAccessLog

def create(url_prefix: str = "") -> APIRouter:
    router = APIRouter(prefix=f"{url_prefix}/stats/v1", tags=["stats"])

    @router.get("/top/{resource_type}")
    def top_assets(resource_type: str, limit: int = 10):
        stmt = (
            select(
                AssetAccessLog.asset_id.label("asset_id"),
                func.count().label("hits"),
            )
            .where(
                AssetAccessLog.resource_type == resource_type,
                AssetAccessLog.status == 200,
            )
            .group_by(AssetAccessLog.asset_id)
            .order_by(func.count().desc())
            .limit(limit)
        )
        with DbSession() as s:
            rows = s.exec(stmt).all()

        # Coerce any Row/tuple shape into JSON-friendly dicts
        out = []
        for r in rows:
            try:
                m = r._mapping  # SQLAlchemy Row
                out.append({"asset_id": m["asset_id"], "hits": int(m["hits"])})
            except Exception:
                asset_id, hits = r  # fallback: tuple
                out.append({"asset_id": asset_id, "hits": int(hits)})
        return out

    return router