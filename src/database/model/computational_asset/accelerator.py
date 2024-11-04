from typing import TYPE_CHECKING
from database.model.field_length import NORMAL
from sqlmodel import Field, SQLModel, Relationship

if TYPE_CHECKING:  # avoid circular imports; only import while type checking
    from database.model.computational_asset.computational_asset import ComputationalAsset


class AcceleratorBase(SQLModel):
    vendor: str | None = Field(
        description="The manufacturer of the Accelerator.",
        max_length=NORMAL,
        schema_extra={"example": "NVIDIA"},
    )
    type: str | None = Field(
        description="Accelerator type.",
        max_length=NORMAL,
        schema_extra={"example": "GPU"},
    )
    model_name: str | None = Field(
        description="The name of the Accelerator model.",
        max_length=NORMAL,
        schema_extra={"example": "A100"},
    )
    architecture: str | None = Field(
        description="The accelerator architecture.",
        max_length=NORMAL,
        schema_extra={"example": "Ampere"},
    )
    cores: int | None = Field(
        description="The number of cores used by the Accelerator.",
        schema_extra={"example": 8},
    )
    memory_gb: float | None = Field(
        description="The Accelerator memory (GB).",
        schema_extra={"example": 64},
    )


class AcceleratorORM(AcceleratorBase, table=True):  # type: ignore [call-arg]
    __tablename__ = "accelerator"
    identifier: int = Field(default=None, primary_key=True)
    computational_asset_identifier: int | None = Field(foreign_key="computational_asset.identifier")
    computational_asset: "ComputationalAsset" = Relationship(back_populates="accelerator")


class Accelerator(AcceleratorBase):
    pass
