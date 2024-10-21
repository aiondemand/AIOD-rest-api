from typing import TYPE_CHECKING
from database.model.field_length import NORMAL
from sqlmodel import Field, SQLModel, Relationship

if TYPE_CHECKING:  # avoid circular imports; only import while type checking
    from database.model.computational_asset.computational_asset import ComputationalAsset

class StorageBase(SQLModel):
  model: str | None = Field(
    description="The full name of the model as provided by the manufacturer.",
    max_length=NORMAL,
    schema_extra={"example": "Model"},
  )
  vendor: str | None = Field(
    description="The manufacturer of the Storage.",
    max_length=NORMAL,
    schema_extra={"example": "AMD"},
  )
  amount: int | None = Field(
    description="The total storage capacity.",
    schema_extra={"example": 1024},
  )
  type: str | None = Field(
    description="Storage type",
    max_length=NORMAL,
    schema_extra={"example": "SSD"},
  )
  read_bandwidth: int | None = Field(
    description="The rate at which data can be retrieved from the storage.",
    schema_extra={"example": 100},
  )
  write_bandwidth: int | None = Field(
    description=("The rate at which data can be transferred form the"
                 " computer and stored onto the storage."),
    schema_extra={"example": 100},
  )

class StorageORM(StorageBase, table=True): # type: ignore [call-arg]
  __tablename__ = "storage"
  identifier: int = Field(default=None, primary_key=True)
  computational_asset_identifier: int | None = Field(foreign_key="computational_asset.identifier")
  computational_asset: "ComputationalAsset" = Relationship(back_populates="storage")
  
  
class Storage(StorageBase):
  pass
  
