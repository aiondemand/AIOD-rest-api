from datetime import datetime
from typing import Type

from sqlalchemy import Column, Integer, ForeignKey
from sqlmodel import Field

from database.model.concept.concept import AIoDConceptBase
from database.model.field_length import LONG, NORMAL, SHORT


class DistributionBase(AIoDConceptBase):
    checksum: str | None = Field(
        description="The value of a checksum algorithm ran on this content.",
        max_length=LONG,
        schema_extra={
            "example": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        },
    )
    checksum_algorithm: str | None = Field(
        description="The checksum algorithm.", max_length=SHORT, schema_extra={"example": "sha256"}
    )
    copyright: str | None = Field(
        max_length=NORMAL,
        schema_extra={"example": "2010-2020 Example Company. All rights reserved."},
    )
    content_url: str = Field(
        max_length=LONG,
        schema_extra={"example": "https://www.example.com/dataset/file.csv"},
    )
    content_size_kb: int | None = Field(schema_extra={"example": 10000})
    date_published: datetime | None = Field(
        description="The datetime (utc) on which this Distribution was first published on an "
        "external platform. ",
        default=None,
        schema_extra={"example": "2022-01-01T15:15:00.000"},
    )
    description: str | None = Field(
        max_length=LONG, schema_extra={"example": "Description of this file."}
    )
    encoding_format: str | None = Field(
        description="The mimetype of this file.",
        max_length=NORMAL,
        schema_extra={"example": "text/csv"},
    )
    name: str | None = Field(max_length=NORMAL, schema_extra={"example": "Name of this file."})
    technology_readiness_level: int | None = Field(
        description="The technology readiness level (TRL) of the distribution. TRL 1 is the "
        "lowest and stands for 'Basic principles observed', TRL 9 is the highest and "
        "stands for 'actual system proven in operational environment'.",
        schema_extra={"example": 1},
    )


def distribution_factory(table_from: str, distribution_name="distribution") -> Type:
    class DistributionORM(DistributionBase, table=True):  # type: ignore [call-arg]
        __tablename__ = f"{distribution_name}_{table_from}"

        identifier: int | None = Field(primary_key=True)

        asset_identifier: int | None = Field(
            sa_column=Column(Integer, ForeignKey(table_from + ".identifier", ondelete="CASCADE"))
        )

    DistributionORM.__name__ = DistributionORM.__qualname__ = f"{distribution_name}_{table_from}"
    return DistributionORM


class Distribution(DistributionBase):
    """All or part of an AIAsset in downloadable form"""
