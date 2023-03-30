"""
Schemas of the AIoD resources.

Note that these objects are different from the ORM objects defined in the database. This leads to
code duplication, so it is not ideal. But it makes it possible to differentiate between the database
objects and the externally used AIoD schemas. The dataset, for example, contains keywords,
which should be a separate object inside a separate table in the database (so that we can easily
search for all datasets having the same keyword). In the external schema, a set of strings is
easier.
"""
from datetime import datetime, timedelta
from typing import Set, List, Optional

from pydantic import BaseModel, Field


class AIoDDistribution(BaseModel):
    content_url: str = Field(max_length=150)
    content_size_kb: int | None
    description: str | None = Field(max_length=5000)
    name: str | None = Field(max_length=150)
    encoding_format: str | None = Field(max_length=150)


class AIoDMeasurementValue(BaseModel):
    variable: str | None
    technique: str | None


class AIoDPublication(BaseModel):
    """The complete metadata of a publication. For now, only a couple of fields are shown,
    we have to decide which fields to use."""

    doi: str | None = Field(max_length=150)
    node_specific_identifier: str = Field(max_length=250)
    node: str = Field(max_length=30)
    id: int | None
    title: str = Field(max_length=250)
    url: str | None = Field(max_length=250)
    datasets: Set[str] = Field(
        description="Identifiers of datasets that are connected to this publication",
        default_factory=list,
    )


class AIoDDataset(BaseModel):
    """
    The complete metadata of a dataset in AIoD format.
    """

    id: int | None
    description: str = Field(max_length=5000)
    name: str = Field(max_length=150)
    node: str = Field(max_length=30)
    node_specific_identifier: str = Field(max_length=250)
    same_as: str = Field(max_length=150)

    # Recommended fields
    creator: str | None = Field(max_length=150)
    date_modified: datetime | None
    date_published: datetime | None
    funder: str | None
    is_accessible_for_free: bool | None
    issn: str | None = Field(max_length=8, min_length=8)
    size: int | None
    spatial_coverage: str | None = Field(max_length=500)
    temporal_coverage_from: datetime | None
    temporal_coverage_to: datetime | None
    version: str | None = Field(max_length=150)

    # Relations
    license: str | None = Field(max_length=150)
    has_parts: Set[str] = Field(
        description="Identifiers of datasets that are part of this " "dataset.",
        default_factory=set,
    )
    is_part: Set[str] = Field(
        description="Identifiers of datasets this dataset is part of.", default_factory=set
    )
    alternate_names: Set[str] = Field(default_factory=set)
    citations: Set[str] | List[AIoDPublication] = Field(
        description="Identifiers of publications linked to this dataset, or the actual "
        "publications",
        default_factory=set,
    )
    distributions: List[AIoDDistribution] = []
    keywords: Set[str] = Field(default_factory=set)
    measured_values: List[AIoDMeasurementValue] = Field(default_factory=list)


class AIoDNews(BaseModel):
    """The complete metadata for news entity"""

    title: str = Field(max_length=500)
    date_modified: datetime
    body: str = Field(max_length=2000)
    headline: str = Field(max_length=500)
    alternative_headline: Optional[str] = Field(max_length=500)
    section: str = Field(max_length=500)
    word_count: int

    media: Optional[list[str]]
    source: Optional[str]
    news_categories: Optional[list[str]]
    business_categories: Optional[list[str]]
    keywords: Optional[list[str]]
    id: int | None


class AIoDEducationalResource(BaseModel):
    """The complete metadata for educational resource"""

    title: str = Field(max_length=500)
    body: str = Field(max_length=500)
    website_url: str = Field(max_length=500)
    date_modified: datetime | None

    educational_level: str = Field(max_length=500)
    educational_type: str = Field(max_length=500)

    pace: str = Field(max_length=500)
    languages: List[str] = Field(
        description="Languages related with an educational resource", default_factory=list
    )
    target_audience: List[str] = Field(
        description="Target audience related with an educational resource", default_factory=list
    )

    educational_use: str | List[str] = Field(
        description="The intended educational use of the resource, such as lecture, lab exercise"
        ", or homework assignment",
        default_factory=str,
    )
    typical_age_range: str | None = Field(max_length=100)

    interactivity_type: str | None = Field(max_length=100)
    accessibility_api: str | None = Field(max_length=100)
    accessibility_control: str | None = Field(max_length=100)
    access_mode: str | None = Field(max_length=100)

    access_mode_sufficient: str | List[str] = Field(
        description="The set of access modes required to access the educational resource,"
        " such as textual and visual.",
        default_factory=str,
    )
    access_restrictions: str | None = Field(max_length=100)
    is_accessible_for_free: bool | None
    time_required: timedelta | None
    citation: str | None = Field(max_length=200)

    version: str | int | None
    credits: bool | None
    number_of_weeks: int | None
    field_prerequisites: str | None = Field(max_length=500)
    short_summary: str | None = Field(max_length=500)
    duration_in_years: int | None

    duration_minutes_and_hours: Optional[str]
    hours_per_week: Optional[str]
    country: Optional[str]

    technical_categories: List[str] = Field(
        description="Technical categories related with an educational resource",
        default_factory=list,
    )
    business_categories: List[str] = Field(
        description="Business categories related with an educational resource", default_factory=list
    )
    keywords: List[str] = Field(
        description="Keywords or tags categories related with an educational resource",
        default_factory=list,
    )

    id: int | None
