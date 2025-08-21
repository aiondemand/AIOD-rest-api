from datetime import datetime, UTC
from sqlmodel import SQLModel, Field

from database.model.field_length import IDENTIFIER_LENGTH


class AssetAccessLog(SQLModel, table=True):  # type: ignore[call-arg]
    __tablename__ = "asset_access_log"
    id: int | None = Field(default=None, primary_key=True)
    asset_id: str = Field(
        max_length=IDENTIFIER_LENGTH, schema_extra=dict(examples=["data_p7v02a70CbBGKk29T8przBjf"])
    )
    resource_type: str = Field(
        max_length=IDENTIFIER_LENGTH, schema_extra=dict(examples=["Datasets", "Models"])
    )
    status: int = Field(description="HTTP Status code of the request.")
    accessed_at: datetime = Field(default_factory=lambda: datetime.now(UTC), index=True)
