import copy

from sqlmodel import Field, Relationship

from database.model.agent.agent_table import AgentTable
from database.model.agent.email import Email
from database.model.agent.telephone import Telephone
from database.model.ai_resource.resource import AIResource, AIResourceBase
from database.model.helper_functions import many_to_many_link_factory, non_abstract_subclasses
from database.model.relationships import OneToOne, ManyToMany

from database.model.serializers import AttributeSerializer, FindByNameDeserializer


class AgentBase(AIResourceBase):
    """
    Many resources, such as organisation and member, are a type of Agent
    and should therefore inherit from this Agent class.
    Shared fields can be defined on this class.
    """


class Agent(AgentBase, AIResource):
    agent_id: int | None = Field(foreign_key=AgentTable.__tablename__ + ".identifier", index=True)
    agent_identifier: AgentTable | None = Relationship()

    telephone: list[Telephone] = Relationship()
    email: list[Email] = Relationship()

    def __init_subclass__(cls):
        """
        Fixing problems with the inheritance of relationships, and creating linking tables.
        The latter cannot be done in the class variables, because it depends on the table-name of
        the child class.
        """
        cls.__annotations__.update(Agent.__annotations__)
        relationships = copy.deepcopy(Agent.__sqlmodel_relationships__)
        cls.update_relationships(relationships)
        for table_to in ("email", "telephone"):
            relationships[table_to].link_model = many_to_many_link_factory(
                table_from=cls.__tablename__, table_to=table_to
            )
        cls.__sqlmodel_relationships__.update(relationships)

    class RelationshipConfig(AIResource.RelationshipConfig):
        agent_identifier: int | None = OneToOne(
            identifier_name="agent_id",
            serializer=AttributeSerializer("identifier"),
            include_in_create=False,
            default_factory_orm=lambda type_: AgentTable(type=type_),
            on_delete_trigger_deletion_by="agent_id",
        )
        email: list[str] = ManyToMany(
            description="A telephone number, including the land code, on which this agent is "
            "reachable.",
            serializer=AttributeSerializer("name"),
            deserializer=FindByNameDeserializer(Email),
            example=["a@b.com"],
            default_factory_pydantic=list,
            on_delete_trigger_orphan_deletion=lambda: [
                f"{a.__tablename__}_email_link" for a in non_abstract_subclasses(Agent)
            ],
        )
        telephone: list[str] = ManyToMany(
            description="A telephone number, including the land code, on which this agent is "
            "reachable.",
            serializer=AttributeSerializer("name"),
            deserializer=FindByNameDeserializer(Telephone),
            example=["0032 XXXX XXXX"],
            default_factory_pydantic=list,
            on_delete_trigger_orphan_deletion=lambda: [
                f"{a.__tablename__}_telephone_link" for a in non_abstract_subclasses(Agent)
            ],
        )
