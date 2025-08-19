from fastapi import APIRouter, Query
from sqlalchemy import func
from sqlmodel import select

from database.session import DbSession
from database.model.access.access_log import AssetAccessLog


def create(url_prefix: str = "") -> APIRouter:
    router = APIRouter(prefix=f"{url_prefix}/stats", tags=["stats"])

    @router.get("/top/{resource_type}")
    def top_assets(resource_type: str, limit: int = Query(10, ge=1, le=1000)):
        stmt = (
            select(
                AssetAccessLog.asset_id,
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

        return [{"asset_id": r[0], "hits": int(r[1])} for r in rows]

    @router.get("/top/all")
    def top_all(limit_per_type: int = Query(20, ge=1, le=1000)):
        ranked = (
            select(
                AssetAccessLog.resource_type,
                AssetAccessLog.asset_id,
                func.count().label("hits"),
                func.row_number()
                .over(
                    partition_by=AssetAccessLog.resource_type,
                    order_by=func.count().desc(),
                )
                .label("rnk"),
            )
            .where(AssetAccessLog.status == 200)
            .group_by(AssetAccessLog.resource_type, AssetAccessLog.asset_id)
        ).subquery("ranked")

        stmt = select(ranked.c.resource_type, ranked.c.asset_id, ranked.c.hits).where(
            ranked.c.rnk <= limit_per_type
        )

        with DbSession() as s:
            rows = s.exec(stmt).all()

        return [{"type": r[0], "asset": r[1], "hits": int(r[2])} for r in rows]

    return router
