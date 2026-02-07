"""Asset upload log for rate limiting.

Tracks user uploads to enforce rate limits within rolling time windows.
Composite index on (user_identifier, created_at) optimizes queries.
"""

from datetime import datetime, UTC

from sqlmodel import SQLModel, Field, Index

from database.model.field_length import NORMAL


class AssetUploadLog(SQLModel, table=True):  # type: ignore[call-arg]
    __tablename__ = "asset_upload_log"
    __table_args__ = (Index("idx_user_time", "user_identifier", "created_at"),)

    id: int | None = Field(default=None, primary_key=True)
    user_identifier: str = Field(max_length=NORMAL, index=True)
    resource_type: str = Field(max_length=NORMAL, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), index=True)
