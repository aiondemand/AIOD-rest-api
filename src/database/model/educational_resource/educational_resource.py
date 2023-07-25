from datetime import datetime
from sqlmodel import Field, Relationship
from typing import List
from database.model.educational_resource.business_categories_link import (
    EducationalResourceBusinessCategoryLink,
)
from database.model.educational_resource.keyword_link import EducationalResourceKeywordLink
from database.model.educational_resource.language_link import EducationalResourceLanguageLink
from database.model.educational_resource.target_audience_link import (
    EducationalResourceTargetAudienceLink,
)
from database.model.educational_resource.technical_categories_link import (
    EducationalResourceTechnicalCategoryLink,
)
from database.model.general.business_category import BusinessCategory
from database.model.general.keyword import Keyword
from database.model.general.language import Language
from database.model.general.target_audience import TargetAudience
from database.model.general.technical_category import TechnicalCategory
from database.model.relationships import ResourceRelationshipList
from serialization import AttributeSerializer, FindByNameDeserializer

from database.model.ai_asset import AIAssetOld


class EducationalResourceBase(AIAssetOld):
    # Required fields
    title: str = Field(max_length=150, schema_extra={"example": "Example News"})
    date_modified: datetime | None = Field(
        default=None, schema_extra={"example": "2022-01-01T15:15:00.000Z"}
    )
    body: str = Field(max_length=500, schema_extra={"example": "Example news body"})
    website_url: str = Field(
        max_length=500,
        schema_extra={"example": "https://example.com/educational_resource/example/website"},
    )
    educational_level: str = Field(
        max_length=500, schema_extra={"example": "Example educational level"}
    )
    educational_type: str = Field(
        max_length=500, schema_extra={"example": "Example educational type"}
    )
    pace: str = Field(max_length=500, schema_extra={"example": "Example pace"})
    # Recommended fields
    interactivity_type: str | None = Field(
        default=None, max_length=500, schema_extra={"example": "Example interactivity type"}
    )
    typical_age_range: str | None = Field(
        default=None, max_length=500, schema_extra={"example": "Example  typical age range"}
    )
    accessibility_api: str | None = Field(
        default=None, max_length=500, schema_extra={"example": "Example accessibility api"}
    )
    accessibility_control: str | None = Field(
        default=None, max_length=500, schema_extra={"example": "Example accessibility control"}
    )
    access_mode: str | None = Field(
        default=None, max_length=500, schema_extra={"example": "Example access mode"}
    )
    access_mode_sufficient: str | None = Field(
        default=None, max_length=500, schema_extra={"example": "Example access mode"}
    )
    access_restrictions: str | None = Field(
        default=None, max_length=500, schema_extra={"example": "Example access restrictions"}
    )
    citations: str | None = Field(
        default=None, max_length=500, schema_extra={"example": "Example citations"}
    )
    version: str | None = Field(
        default=None, max_length=500, schema_extra={"example": "Example version"}
    )
    number_of_weeks: int | None = Field(default=None, schema_extra={"example": 0})
    field_prerequisites: str | None = Field(
        default=None, max_length=500, schema_extra={"example": "Example field prerequisites"}
    )
    short_summary: str | None = Field(
        default=None, max_length=500, schema_extra={"example": "Example short summary"}
    )
    duration_minutes_and_hours: str | None = Field(
        default=None, max_length=500, schema_extra={"example": "Example duration minutes and hours"}
    )
    hours_per_week: str | None = Field(
        default=None, max_length=500, schema_extra={"example": "Example hours per week"}
    )
    country: str | None = Field(
        default=None, max_length=500, schema_extra={"example": "Example country"}
    )
    is_accessible_for_free: bool = Field(default=True, schema_extra={"example": True})
    credits: bool = Field(default=True, schema_extra={"example": True})
    duration_in_years: int | None = Field(default=None, schema_extra={"example": 0})


class EducationalResource(EducationalResourceBase, table=True):  # type: ignore [call-arg]
    __tablename__ = "educational_resource"
    identifier: int = Field(primary_key=True, foreign_key="ai_asset.identifier")
    languages: List[Language] = Relationship(
        back_populates="educational_resources", link_model=EducationalResourceLanguageLink
    )
    target_audience: List[TargetAudience] = Relationship(
        back_populates="educational_resources", link_model=EducationalResourceTargetAudienceLink
    )
    keywords: List[Keyword] = Relationship(
        back_populates="educational_resources", link_model=EducationalResourceKeywordLink
    )

    business_categories: List[BusinessCategory] = Relationship(
        back_populates="educational_resources", link_model=EducationalResourceBusinessCategoryLink
    )
    technical_categories: List[TechnicalCategory] = Relationship(
        back_populates="educational_resources", link_model=EducationalResourceTechnicalCategoryLink
    )

    class RelationshipConfig:
        languages: List[str] = ResourceRelationshipList(
            example=["language 1", "language 2"],
            serializer=AttributeSerializer("name"),
            deserializer=FindByNameDeserializer(Language),
        )
        target_audience: List[str] = ResourceRelationshipList(
            example=["target audience 1", "target audience 2"],
            serializer=AttributeSerializer("name"),
            deserializer=FindByNameDeserializer(TargetAudience),
        )
        keywords: List[str] = ResourceRelationshipList(
            serializer=AttributeSerializer("name"),
            deserializer=FindByNameDeserializer(Keyword),
            example=["keyword1", "keyword2"],
        )
        business_categories: List[str] = ResourceRelationshipList(
            example=["business category 1", "business category 2"],
            serializer=AttributeSerializer("name"),
            deserializer=FindByNameDeserializer(BusinessCategory),
        )
        technical_categories: List[str] = ResourceRelationshipList(
            example=["technical category 1", "technical category 2"],
            serializer=AttributeSerializer("name"),
            deserializer=FindByNameDeserializer(TechnicalCategory),
        )
