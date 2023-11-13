from typing import Type

from sqlalchemy import Column, Integer, ForeignKey
from sqlmodel import Field

from database.model.ai_asset.distribution import DistributionBase
from database.model.field_length import NORMAL, LONG


class RunnableDistributionBase(DistributionBase):
    installation_script: str | None = Field(
        description="An url pointing to a script that can be run to setup the environment "
        "necessary for running this distribution. This can be a relative url, if this "
        "distribution is a file archive.",
        max_length=NORMAL,
        default=None,
        schema_extra={"example": "./install.sh"},
    )
    installation: str | None = Field(
        description="A human readable explanation of the installation, primarily meant as "
        "alternative for when there is no installation script.",
        max_length=LONG,
        default=None,
        schema_extra={"example": "Build the Dockerfile"},
    )
    installation_time_milliseconds: int | None = Field(
        description="An illustrative time that the installation might typically take.",
        schema_extra={"example": 100},
    )
    deployment_script: str | None = Field(
        description="An url pointing to a script that can be run to use this resource. This can "
        "be a relative url, if this distribution is a file archive.",
        max_length=NORMAL,
        default=None,
        schema_extra={"example": "./run.sh"},
    )
    deployment: str | None = Field(
        description="A human readable explanation of the deployment, primarily meant as "
        "alternative for when there is no installation script.",
        max_length=LONG,
        default=None,
        schema_extra={
            "example": "You can run the run.py file using python3. See README.md for "
            "required arguments."
        },
    )
    deployment_time_milliseconds: int | None = Field(
        description="An illustrative time that the deployment might typically take.",
        schema_extra={"example": 100},
    )
    os_requirement: str | None = Field(
        description="A human readable explanation for the required os.",
        max_length=NORMAL,
        default=None,
        schema_extra={"example": "Windows 11."},
    )
    dependency: str | None = Field(
        description="A human readable explanation of (software) dependencies.",
        max_length=NORMAL,
        default=None,
        schema_extra={"example": "Python packages as listed in requirements.txt."},
    )
    hardware_requirement: str | None = Field(
        description="A human readable explanation of hardware requirements.",
        max_length=NORMAL,
        default=None,
        schema_extra={"example": "4GB RAM; 100MB storage; 1GHz processor with 8 cores."},
    )


def runnable_distribution_factory(table_from: str, distribution_name="distribution") -> Type:
    class RunnableDistributionORM(RunnableDistributionBase, table=True):  # type: ignore [call-arg]
        __tablename__ = f"{distribution_name}_{table_from}"

        identifier: int | None = Field(primary_key=True)

        asset_identifier: int | None = Field(
            sa_column=Column(Integer, ForeignKey(table_from + ".identifier", ondelete="CASCADE"))
        )

    RunnableDistributionORM.__name__ = (
        RunnableDistributionORM.__qualname__
    ) = f"{distribution_name}_{table_from}"
    return RunnableDistributionORM


class RunnableDistribution(RunnableDistributionBase):
    """All or part of an AIAsset in downloadable form"""
