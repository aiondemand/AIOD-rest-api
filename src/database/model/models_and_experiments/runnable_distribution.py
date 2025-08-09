from typing import Type

from pydantic import create_model
from sqlalchemy import Column, Integer, ForeignKey, String
from sqlmodel import Field

from database.model.ai_asset.distribution import DistributionBase
from database.model.field_length import NORMAL, LONG, IDENTIFIER_LENGTH


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
    # Made content_url optional for ML Models because it could just be a script,
    # not necessary to have a url.
    content_url: str | None = Field(
        max_length=NORMAL,
        schema_extra={"example": "https://www.example.com/mlmodel/file.csv"},
    )  # type: ignore


def runnable_distribution_factory(table_from: str, distribution_name="distribution") -> Type:
    RunnableDistributionORM = create_model(
        f"{distribution_name}_{table_from}",
        __base__=(RunnableDistributionBase,),
        __cls_kwargs__=dict(table=True),
        identifier=(int | None, Field(primary_key=True)),
        asset_identifier=(
            str | None,
            Field(
                sa_column=Column(
                    String(IDENTIFIER_LENGTH),
                    ForeignKey(table_from + ".identifier", ondelete="CASCADE"),
                )
            ),
        ),
    )
    # Pydantic will issue a warning for non-default dunder attributes, so we add it after creation
    RunnableDistributionORM.__tablename__ = f"{distribution_name}_{table_from}"
    return RunnableDistributionORM


class RunnableDistribution(RunnableDistributionBase):
    """All or part of an AIAsset in downloadable form"""
