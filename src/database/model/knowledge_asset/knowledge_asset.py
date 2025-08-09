import copy

from sqlalchemy import ForeignKey
from sqlmodel import Field, Relationship

from database.model.ai_asset.ai_asset import AIAssetBase, AIAsset
from database.model.ai_asset.ai_asset_table import AIAssetTable
from database.model.helper_functions import many_to_many_link_factory
from database.model.knowledge_asset.knowledge_asset_table import KnowledgeAssetTable
from database.model.relationships import ManyToMany, OneToOne
from database.model.serializers import AttributeSerializer, FindByIdentifierDeserializerList
from database.model.field_length import IDENTIFIER_LENGTH


class KnowledgeAssetBase(AIAssetBase):
    pass


class KnowledgeAsset(KnowledgeAssetBase, AIAsset):
    knowledge_asset_id: str | None = Field(
        max_length=IDENTIFIER_LENGTH,
        # Initializing `sa_column` instead doesn't work. Perhaps because it'd be used twice?
        sa_column_args=[
            ForeignKey(KnowledgeAssetTable.__tablename__ + ".identifier", onupdate="CASCADE")
        ],
        sa_column_kwargs=dict(nullable=True, index=True, unique=True),
    )
    knowledge_asset_identifier: KnowledgeAssetTable | None = Relationship()

    documents: list[AIAssetTable] = Relationship()

    def __init_subclass__(cls):
        """
        Fixing problems with the inheritance of relationships, and creating linking tables.
        The latter cannot be done in the class variables, because it depends on the table-name of
        the child class.
        """
        cls.__annotations__.update(KnowledgeAsset.__annotations__)
        relationships = copy.deepcopy(KnowledgeAsset.__sqlmodel_relationships__)
        cls.update_relationships_asset(relationships)

        relationships["documents"].link_model = many_to_many_link_factory(
            table_from=cls.__tablename__,
            table_to="ai_asset",
            table_prefix="documents",
            from_identifier_type=str,
            to_identifier_type=str,
        )
        cls.__sqlmodel_relationships__.update(relationships)

    class RelationshipConfig(AIAsset.RelationshipConfig):
        documents: list[str] = ManyToMany(
            description="The identifier of an AI asset for which the Knowledge Asset acts as an "
            "information source",
            _serializer=AttributeSerializer("identifier"),
            deserializer=FindByIdentifierDeserializerList(AIAssetTable),
            example=[],
            default_factory_pydantic=list,
        )
        knowledge_asset_identifier: str | None = OneToOne(
            identifier_name="knowledge_asset_id",
            _serializer=AttributeSerializer("identifier"),
            include_in_create=False,
            default_factory_orm=lambda type_: KnowledgeAssetTable(type=type_),
            on_delete_trigger_deletion_by="knowledge_asset_id",
        )
