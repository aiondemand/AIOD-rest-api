from typing import TYPE_CHECKING
from database.model.field_length import NORMAL
from sqlmodel import Field, SQLModel, Relationship

if TYPE_CHECKING:  # avoid circular imports; only import while type checking
    from database.model.computational_asset.computational_asset import ComputationalAsset


class CpuBase(SQLModel):
  num_cpu_cores: int | None = Field(
    description="The number of cores used by the CPU.",
    schema_extra={"example": 8},
  )
  architecture: str | None = Field(
    description="The CPU architecture.",
    max_length=NORMAL,
    schema_extra={"example": "ARM"},
  )
  vendor: str | None = Field(
    description="The manufacturer of the CPU.",
    max_length=NORMAL,
    schema_extra={"example": "CPU_AMD"},
  )
  model_name: str | None = Field(
    description="The name of the CPU model.",
    max_length=NORMAL,
    schema_extra={"example": "Athlon"},
  )
  cpu_family: str | None = Field(
    description="The family in which the CPU model belongs.",
    max_length=NORMAL,
    schema_extra={"example": "Athlon"},
  )
  clock_speed: int | None = Field(
    description="The CPU clock speed.",
    schema_extra={"example": 3.2},
  )
  
class CpuORM(CpuBase, table=True):
  __tablename__ = "cpu"
  identifier: int = Field(default=None, primary_key=True)
  computational_asset_identifier: int | None = Field(foreign_key="computational_asset.identifier")
  computational_asset: "ComputationalAsset" = Relationship(back_populates="cpu")
  

class Cpu(CpuBase):
  pass