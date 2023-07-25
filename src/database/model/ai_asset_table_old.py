from sqlmodel import SQLModel, Field


class AIAssetOldTable(SQLModel, table=True):  # type: ignore [call-arg]
    __tablename__ = "ai_asset_old"

    """
    Many resources, such as dataset and publication, are a type of AIAsset
    and should therefore inherit from this AIAsset class.
    Shared fields can be defined on this class.

    Notice the difference between AIAsset and AIAssetOldTable.
    The latter enables defining a relationship to "any AI Asset",
    by making sure that the identifiers of all resources that
    are AIAssets, are unique over the AIAssets.
    """
    identifier: int = Field(
        default=None,
        primary_key=True,
        description="The identifier of each asset should be the same as this identifier",
    )
    type: str = Field(
        description="The name of the table of the asset. E.g. 'dataset' or 'publication'"
    )
