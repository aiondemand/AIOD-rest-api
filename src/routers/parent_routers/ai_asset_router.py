from typing import Type

from database.model.ai_asset.ai_asset import AIAsset
from database.model.ai_asset.ai_asset_table import AIAssetTable
from routers.parent_router import ParentRouter


class AIAssetRouter(ParentRouter):
    @property
    def resource_name(self) -> str:
        return "ai_asset"

    @property
    def resource_name_plural(self) -> str:
        return "ai_assets"

    @property
    def parent_class(self) -> Type[AIAsset]:
        return AIAsset

    @property
    def parent_class_table(self) -> Type[AIAssetTable]:
        return AIAssetTable
