import copy

from sqlalchemy import ForeignKey
from sqlmodel import Field, Relationship

from database.model.agent.agent_table import AgentTable
from database.model.ai_resource.resource import AIResourceBase, AIResource
from database.model.relationships import OneToOne
from database.model.serializers import AttributeSerializer
from database.model.field_length import IDENTIFIER_LENGTH


class AgentBase(AIResourceBase):
    """
    Many resources, such as organisation and member, are a type of Agent
    and should therefore inherit from this Agent class.
    Shared fields can be defined on this class.
    """


class Agent(AgentBase, AIResource):
    agent_id: str | None = Field(
        # Initializing `sa_column` instead doesn't work. Perhaps because it'd be used twice?
        # default_factory=generate_id_with_prefix(),
        max_length=IDENTIFIER_LENGTH,
        sa_column_args=[ForeignKey(AgentTable.__tablename__ + ".identifier", onupdate="CASCADE")],
        sa_column_kwargs=dict(nullable=True, index=True),
    )
    agent_identifier: AgentTable | None = Relationship()

    def __init_subclass__(cls):
        """
        Fixing problems with the inheritance of relationships, and creating linking tables.
        The latter cannot be done in the class variables, because it depends on the table-name of
        the child class.
        """
        cls.__annotations__.update(Agent.__annotations__)
        relationships = copy.deepcopy(Agent.__sqlmodel_relationships__)
        cls.update_relationships(relationships)
        cls.__sqlmodel_relationships__.update(relationships)

    class RelationshipConfig(AIResource.RelationshipConfig):
        agent_identifier: str | None = OneToOne(
            identifier_name="agent_id",
            _serializer=AttributeSerializer("identifier"),
            include_in_create=False,
            default_factory_orm=lambda type_: AgentTable(type=type_),
            on_delete_trigger_deletion_by="agent_id",
        )
