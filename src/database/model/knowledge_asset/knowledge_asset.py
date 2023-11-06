import copy

from sqlmodel import Field, Relationship

from database.model.ai_asset.ai_asset import AIAssetBase, AIAsset
from database.model.ai_asset.ai_asset_table import AIAssetTable
from database.model.helper_functions import many_to_many_link_factory
from database.model.knowledge_asset.knowledge_asset_table import KnowledgeAssetTable
from database.model.relationships import ManyToMany
from database.model.serializers import AttributeSerializer, FindByIdentifierDeserializer


class KnowledgeAssetBase(AIAssetBase):
    pass


class KnowledgeAsset(KnowledgeAssetBase, AIAsset):
    knowledge_asset_id: int | None = Field(
        foreign_key=KnowledgeAssetTable.__tablename__ + ".identifier", index=True
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
            table_from=cls.__tablename__, table_to="ai_asset", table_prefix="documents"
        )
        cls.__sqlmodel_relationships__.update(relationships)

    class RelationshipConfig(AIAsset.RelationshipConfig):
        documents: list[int] = ManyToMany(
            description="The identifier of an AI asset for which the Knowledge Asset acts as an "
            "information source",
            serializer=AttributeSerializer("identifier"),
            deserializer=FindByIdentifierDeserializer(AIAssetTable),
            example=[],
            default_factory_pydantic=list,
        )
