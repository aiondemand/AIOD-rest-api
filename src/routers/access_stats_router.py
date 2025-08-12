from typing import List

from fastapi import APIRouter
from sqlalchemy import func
from sqlmodel import SQLModel, Field, select

from database.session import DbSession
from database.model.access.access_log import AssetAccessLog


class TopAsset(SQLModel):
    asset_id: str = Field()
    hits: int = Field()


def create(url_prefix: str = "") -> APIRouter:
    router = APIRouter(prefix=f"{url_prefix}/stats", tags=["stats"])

    @router.get("/top/{resource_type}", response_model=List[TopAsset])
    def top_assets(resource_type: str, limit: int = 10) -> List[TopAsset]:
        hits_count = func.count(AssetAccessLog.id).label("hits")

        stmt = (
            select(AssetAccessLog.asset_id, hits_count)
            .where(
                AssetAccessLog.resource_type == resource_type,
                AssetAccessLog.status == 200,
            )
            .group_by(AssetAccessLog.asset_id)
            .order_by(hits_count.desc())
            .limit(limit)
        )

        with DbSession() as s:
            rows = s.exec(stmt).all()
        return [TopAsset(asset_id=a, hits=int(h)) for a, h in rows]

    return router
