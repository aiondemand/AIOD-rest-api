from typing import TYPE_CHECKING
from database.model.field_length import NORMAL
from sqlmodel import Field, SQLModel, Relationship

if TYPE_CHECKING:  # avoid circular imports; only import while type checking
    from database.model.computational_asset.computational_asset import ComputationalAsset

class MemoryBase(SQLModel):
  type: str | None = Field(
    description="Memory type",
    max_length=NORMAL,
    schema_extra={"example": "RAM"},
  )
  amount_gb: int | None = Field(
    description="The total memory capacity measured in Gigabytes.",
    schema_extra={"example": 16},
  )
  read_bandwidth: int | None = Field(
    description="The rate at which data can be retrieved.",
    schema_extra={"example": 100},
  )
  write_bandwidth: int | None = Field(
    description="The rate at which data can be stored",
    schema_extra={"example": 100},
  )
  rdma: str | None = Field(
    description="Technology that enables two networked computers to exchange data in main memory.",
    max_length=NORMAL,
    schema_extra={"example": ""},
  )

class MemoryORM(MemoryBase, table=True): # type: ignore [call-arg]
  __tablename__ = "memory"
  identifier: int = Field(default=None, primary_key=True)
  computational_asset_identifier: int | None = Field(foreign_key="computational_asset.identifier")
  computational_asset: "ComputationalAsset" = Relationship(back_populates="memory")
  
  
class Memory(MemoryBase):
  pass