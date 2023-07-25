from datetime import datetime

from sqlmodel import Field, Relationship, SQLModel

from database.model.agent_table import AgentTable
from database.model.ai_asset import AIAssetOld
from database.model.computational_resource.alternate_name import (
    ComputationalResourceAlternateNameLink,
    ComputationalResourceAlternateName,
)
from database.model.computational_resource.application_area_link import (
    ComputationalResourceApplicationAreaLink,
)
from database.model.computational_resource.capability import (
    ComputationalResourceCapabilityLink,
    ComputationalResourceCapability,
)
from database.model.computational_resource.citation import (
    ComputationalResourceCitationLink,
    ComputationalResourceCitation,
)
from database.model.computational_resource.contact_link import ComputationalResourceContactLink
from database.model.computational_resource.creator_link import ComputationalResourceCreatorLink
from database.model.computational_resource.distribution import (
    ComputationalResourceDistribution,
    ComputationalResourceDistributionOrm,
)
from database.model.computational_resource.endpoint import (
    ComputationalResourceEndpointOrm,
)
from database.model.computational_resource.has_endpoint_link import (
    ComputationalResourceHasEndpointLink,
)
from database.model.computational_resource.has_share_link import ComputationalResourceHasShareLink
from database.model.computational_resource.keyword_link import (
    ComputationalResourceKeywordLink,
)
from database.model.computational_resource.managed_by_link import ComputationalResourceManagedByLink
from database.model.computational_resource.otherinfo import (
    ComputationalResourceOtherInfoLink,
    ComputationalResourceOtherInfo,
)
from database.model.computational_resource.research_area_link import (
    ComputationalResourceResearchAreaLink,
)
from database.model.computational_resource.service_link import ComputationalResourceServiceLink
from database.model.computational_resource.status_info_link import (
    ComputationalResourceStatusInfoLink,
)
from database.model.computational_resource.uri import (
    ComputationalResourceUriOrm,
)
from database.model.general.application_areas import ApplicationArea
from database.model.general.keyword import Keyword
from database.model.general.research_areas import ResearchArea
from database.model.relationships import ResourceRelationshipList
from serialization import (
    CastDeserializer,
    FindByIdentifierDeserializer,
    FindByNameDeserializer,
    AttributeSerializer,
)


class ComputationalResourceParentChildLink(SQLModel, table=True):  # type: ignore [call-arg]
    __tablename__ = "computational_resource_parent_child_link"
    parent_identifier: int = Field(
        foreign_key="computational_resource.identifier", primary_key=True
    )
    child_identifier: int = Field(foreign_key="computational_resource.identifier", primary_key=True)


class ComputationalResourceBase(AIAssetOld):
    # Required fields
    name: str = Field(max_length=150, schema_extra={"example": "Human-readable name"})

    # Recommended fields
    description: str | None = Field(max_length=5000, schema_extra={"example": "description"})
    logo: str | None = Field(
        max_length=250,
        schema_extra={"example": "https://www.example.com/computational_resource/example"},
    )
    creationTime: datetime | None = Field(
        default=None, schema_extra={"example": "2022-01-01T15:15:00.000Z"}
    )
    validity: int | None = Field(
        schema_extra={"example": 22},
        description="The duration (in seconds) after CreationTime that the information presented "
        "in the Entity SHOULD be considered relevant. After that period has elapsed, "
        "the information SHOULD NOT be considered relevant.",
    )
    complexity: str | None = Field(
        max_length=250,
        schema_extra={"example": "endpointType=X, share=Y, resource=Z."},
        description="Human-readable summary description of the complexity in terms of the number "
        "of endpoint types, shares and resources. The syntax should be: "
        "endpointType=X, share=Y, resource=Z.",
    )
    location: str | None = Field(
        max_length=500, schema_extra={"example": "http://www.example.com/endpoint"}
    )
    type: str | None = Field(max_length=500, schema_extra={"example": "AWS::ECS::Cluster"})

    qualityLevel: str | None = Field(max_length=500, schema_extra={"example": "test"})


class ComputationalResource(ComputationalResourceBase, table=True):  # type: ignore [call-arg]
    __tablename__ = "computational_resource"

    identifier: int = Field(primary_key=True, foreign_key="ai_asset.identifier")

    alternateName: list[ComputationalResourceAlternateName] = Relationship(
        back_populates="computational_resources", link_model=ComputationalResourceAlternateNameLink
    )
    capability: list[ComputationalResourceCapability] = Relationship(
        back_populates="computational_resources", link_model=ComputationalResourceCapabilityLink
    )
    citation: list[ComputationalResourceCitation] = Relationship(
        back_populates="computational_resources", link_model=ComputationalResourceCitationLink
    )
    distribution: list[ComputationalResourceDistributionOrm] = Relationship(
        sa_relationship_kwargs={"cascade": "all, delete"}
    )
    statusInfo: list[ComputationalResourceUriOrm] = Relationship(
        sa_relationship_kwargs={"cascade": "all, delete"},
        link_model=ComputationalResourceStatusInfoLink,
    )
    hasShare: list[ComputationalResourceUriOrm] = Relationship(
        sa_relationship_kwargs={"cascade": "all, delete"},
        link_model=ComputationalResourceHasShareLink,
    )
    service: list[ComputationalResourceUriOrm] = Relationship(
        sa_relationship_kwargs={"cascade": "all, delete"},
        link_model=ComputationalResourceServiceLink,
    )
    hasEndpoint: list[ComputationalResourceEndpointOrm] = Relationship(
        sa_relationship_kwargs={"cascade": "all, delete"},
        link_model=ComputationalResourceHasEndpointLink,
    )

    keyword: list[Keyword] = Relationship(
        back_populates="computational_resources", link_model=ComputationalResourceKeywordLink
    )
    otherInfo: list[ComputationalResourceOtherInfo] = Relationship(
        back_populates="computational_resources", link_model=ComputationalResourceOtherInfoLink
    )
    researchArea: list[ResearchArea] = Relationship(
        back_populates="computational_resources", link_model=ComputationalResourceResearchAreaLink
    )
    applicationArea: list[ApplicationArea] = Relationship(
        back_populates="computational_resources",
        link_model=ComputationalResourceApplicationAreaLink,
    )

    creator: list[AgentTable] = Relationship(link_model=ComputationalResourceCreatorLink)
    contact: list[AgentTable] = Relationship(link_model=ComputationalResourceContactLink)
    managedBy: list[AgentTable] = Relationship(link_model=ComputationalResourceManagedByLink)
    hasPart: list["ComputationalResource"] = Relationship(
        back_populates="isPartOf",
        link_model=ComputationalResourceParentChildLink,
        sa_relationship_kwargs=dict(
            primaryjoin="ComputationalResource.identifier==ComputationalResourceParentChildLink.parent_identifier",  # noqa E501
            secondaryjoin="ComputationalResource.identifier==ComputationalResourceParentChildLink.child_identifier",  # noqa E501
        ),
    )
    isPartOf: list["ComputationalResource"] = Relationship(
        back_populates="hasPart",
        link_model=ComputationalResourceParentChildLink,
        sa_relationship_kwargs=dict(
            primaryjoin="ComputationalResource.identifier==ComputationalResourceParentChildLink.child_identifier",  # noqa E501
            secondaryjoin="ComputationalResource.identifier==ComputationalResourceParentChildLink.parent_identifier",  # noqa E501
        ),
    )

    class RelationshipConfig:  # This is AIoD-specific code, used to go from Pydantic to SqlAlchemy
        alternateName: list[str] = ResourceRelationshipList(
            serializer=AttributeSerializer("name"),
            deserializer=FindByNameDeserializer(ComputationalResourceAlternateName),
            example=["alias1", "alias2"],
        )
        capability: list[str] = ResourceRelationshipList(
            serializer=AttributeSerializer("name"),
            deserializer=FindByNameDeserializer(ComputationalResourceCapability),
            description="The provided capability according to the Open Grid Service Architecture ("
            "OGSA) architecture [OGF-GFD80]",
            example=["monitoring_and_analytics", "resource_management", "security_framework"],
        )
        # Is there a URI type that we can reuse here instead of string?
        citation: list[str] = ResourceRelationshipList(
            serializer=AttributeSerializer("name"),
            deserializer=FindByNameDeserializer(ComputationalResourceCitation),
            description="A bibliographic reference for the AI asset.",
            example=[]  # No examples added, I think we should change it to a relationship to
            # Publication later (added a comment on the spreadsheet)
        )
        keyword: list[str] = ResourceRelationshipList(
            serializer=AttributeSerializer("name"),
            deserializer=FindByNameDeserializer(Keyword),
            description="terms or phrases providing additional context for the AI asset.",
            example=["keyword1", "keyword2"],
        )
        otherInfo: list[str] = ResourceRelationshipList(
            serializer=AttributeSerializer("name"),
            deserializer=FindByNameDeserializer(ComputationalResourceOtherInfo),
            description="Placeholder to publish info that does not fit in any other attribute. "
            "Free-form string, comma-separated tags, (name, value ) pair are all "
            "examples of valid syntax ",
            example=["Free-format text"],
        )
        researchArea: list[str] = ResourceRelationshipList(
            serializer=AttributeSerializer("name"),
            deserializer=FindByNameDeserializer(ResearchArea),
            example=["Fraud Prevention", "Voice Assistance", "Disease Classification"],
        )
        applicationArea: list[str] = ResourceRelationshipList(
            serializer=AttributeSerializer("name"),
            deserializer=FindByNameDeserializer(ApplicationArea),
            example=["Anomaly Detection", "Voice Recognition", "Computer Vision"],
        )
        isPartOf: list[int] = ResourceRelationshipList(
            example=[],
            serializer=AttributeSerializer("identifier"),
        )
        hasPart: list[int] = ResourceRelationshipList(
            example=[],
            serializer=AttributeSerializer("identifier"),
        )
        creator: list[int] = ResourceRelationshipList(
            example=[],
            serializer=AttributeSerializer("identifier"),
            deserializer=FindByIdentifierDeserializer(AgentTable),
        )
        contact: list[int] = ResourceRelationshipList(
            example=[],
            serializer=AttributeSerializer("identifier"),
            deserializer=FindByIdentifierDeserializer(AgentTable),
        )
        managedBy: list[int] = ResourceRelationshipList(
            example=[],
            serializer=AttributeSerializer("identifier"),
            deserializer=FindByIdentifierDeserializer(AgentTable),
        )
        distribution: list[ComputationalResourceDistribution] = ResourceRelationshipList(
            deserializer=CastDeserializer(ComputationalResourceDistributionOrm)
        )
        statusInfo: list[str] = ResourceRelationshipList(
            deserializer=FindByNameDeserializer(ComputationalResourceUriOrm),
            serializer=AttributeSerializer(attribute_name="name"),
            example=["www.example.com/resource/status-page"],
        )
        hasShare: list[str] = ResourceRelationshipList(
            deserializer=FindByNameDeserializer(ComputationalResourceUriOrm),
            serializer=AttributeSerializer(attribute_name="name"),
        )
        service: list[str] = ResourceRelationshipList(
            deserializer=FindByNameDeserializer(ComputationalResourceUriOrm),
            serializer=AttributeSerializer(attribute_name="name"),
            example=["www.example.com/resource/other_service"],
        )
        hasEndpoint: list[str] = ResourceRelationshipList(
            deserializer=FindByNameDeserializer(ComputationalResourceEndpointOrm),
            serializer=AttributeSerializer(attribute_name="name"),
            example=["http://www.example.com/endpoint"],
        )
        # TODO add documentIn, KnowledgeAsset should be implemented first.


# Defined separate because it references ComputationalResource,
# and can therefor not be defined inside ComputationalResource
deserializer = FindByIdentifierDeserializer(ComputationalResource)
ComputationalResource.RelationshipConfig.isPartOf.deserializer = deserializer  # type: ignore[attr-defined] # noqa E501
ComputationalResource.RelationshipConfig.hasPart.deserializer = deserializer  # type: ignore[attr-defined]  # noqa E501
