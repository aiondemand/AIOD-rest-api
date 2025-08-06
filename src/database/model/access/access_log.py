from datetime import datetime
from sqlmodel import SQLModel, Field

class AssetAccessLog(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    asset_id: str
    resource_type: str           # “datasets”, “models”, etc.
    status: int                  # HTTP status code
    accessed_at: datetime = Field(default_factory=datetime.utcnow, index=True)
