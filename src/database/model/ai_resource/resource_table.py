"""
The AIResource table, which is linked to every child of the AbstractAIResource (e.g. Dataset).
"""

from sqlmodel import SQLModel, Field, Relationship


class AIResourcePartLink(SQLModel, table=True):  # type: ignore [call-arg]
    __tablename__ = "ai_resource_part_link"
    parent_identifier: int = Field(foreign_key="ai_resource.identifier", primary_key=True)
    child_identifier: int = Field(foreign_key="ai_resource.identifier", primary_key=True)


class AIResourceRelevantLink(SQLModel, table=True):  # type: ignore [call-arg]
    __tablename__ = "ai_resource_relevant_link"
    parent_identifier: int = Field(foreign_key="ai_resource.identifier", primary_key=True)
    relevant_identifier: int = Field(foreign_key="ai_resource.identifier", primary_key=True)


class AIResourceBase(SQLModel):
    pass


class AIResourceORM(AIResourceBase, table=True):  # type: ignore [call-arg]
    __tablename__ = "ai_resource"
    identifier: int = Field(default=None, primary_key=True)
    type: str = Field(default="will be overwritten by resource_router")

    is_part_of: list["AIResourceORM"] = Relationship(
        back_populates="has_part",
        link_model=AIResourcePartLink,
        sa_relationship_kwargs={
            "primaryjoin": "AIResourceORM.identifier==AIResourcePartLink.parent_identifier",
            "secondaryjoin": "AIResourceORM.identifier==AIResourcePartLink.child_identifier",
        },
    )
    has_part: list["AIResourceORM"] = Relationship(
        back_populates="is_part_of",
        link_model=AIResourcePartLink,
        sa_relationship_kwargs={
            "primaryjoin": "AIResourceORM.identifier==AIResourcePartLink.child_identifier",
            "secondaryjoin": "AIResourceORM.identifier==AIResourcePartLink.parent_identifier",
        },
    )
    relevant_resource: list["AIResourceORM"] = Relationship(
        back_populates="relevant_to",
        link_model=AIResourceRelevantLink,
        sa_relationship_kwargs={
            "primaryjoin": "AIResourceORM.identifier==AIResourceRelevantLink.relevant_identifier",
            "secondaryjoin": "AIResourceORM.identifier==AIResourceRelevantLink.parent_identifier",
        },
    )
    relevant_to: list["AIResourceORM"] = Relationship(
        back_populates="relevant_resource",
        link_model=AIResourceRelevantLink,
        sa_relationship_kwargs={
            "primaryjoin": "AIResourceORM.identifier==AIResourceRelevantLink.parent_identifier",
            "secondaryjoin": "AIResourceORM.identifier==AIResourceRelevantLink.relevant_identifier",
        },
    )
