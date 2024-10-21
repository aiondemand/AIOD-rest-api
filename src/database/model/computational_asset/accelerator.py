from typing import TYPE_CHECKING
from database.model.field_length import NORMAL
from sqlmodel import Field, SQLModel, Relationship

if TYPE_CHECKING:  # avoid circular imports; only import while type checking
    from database.model.computational_asset.computational_asset import ComputationalAsset


class AcceleratorBase(SQLModel):
    vendor: str | None = Field(
        description="The manufacturer of the Accelerator.",
        max_length=NORMAL,
        schema_extra={"example": "CPU_AMD"},
    )
    type: str | None = Field(
        description="Accelerator type.",
        max_length=NORMAL,
        schema_extra={"example": "type"},
    )
    model_name: str | None = Field(
        description="The name of the Accelerator model.",
        max_length=NORMAL,
        schema_extra={"example": "Athlon"},
    )
    architecture: str | None = Field(
        description="The accelerator architecture.",
        max_length=NORMAL,
        schema_extra={"example": "ARM"},
    )
    cores: int | None = Field(
        description="The number of cores used by the Accelerator.",
        schema_extra={"example": 8},
    )
    memory: int | None = Field(
        description="The Accelerator memory.",
        schema_extra={"example": 64},
    )


class AcceleratorORM(AcceleratorBase, table=True):  # type: ignore [call-arg]
    __tablename__ = "accelerator"
    identifier: int = Field(default=None, primary_key=True)
    computational_asset_identifier: int | None = Field(foreign_key="computational_asset.identifier")
    computational_asset: "ComputationalAsset" = Relationship(back_populates="accelerator")


class Accelerator(AcceleratorBase):
    pass
