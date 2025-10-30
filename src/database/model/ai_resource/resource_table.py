"""
The AIResource table, which is linked to every child of the AbstractAIResource (e.g. Dataset).
"""

from sqlalchemy import ForeignKey
from sqlmodel import SQLModel, Field, Relationship

from database.model.field_length import IDENTIFIER_LENGTH
from database.identifiers import create_id_generator


class AIResourcePartLink(SQLModel, table=True):  # type: ignore [call-arg]
    __tablename__ = "ai_resource_part_link"
    parent_identifier: str = Field(
        max_length=IDENTIFIER_LENGTH,
        sa_column_args=[
            ForeignKey("ai_resource.identifier", onupdate="CASCADE", ondelete="CASCADE")
        ],
        sa_column_kwargs=dict(nullable=True, index=True),
        primary_key=True,
    )
    child_identifier: str = Field(
        max_length=IDENTIFIER_LENGTH,
        sa_column_args=[
            ForeignKey("ai_resource.identifier", onupdate="CASCADE", ondelete="CASCADE")
        ],
        sa_column_kwargs=dict(nullable=True, index=True),
        primary_key=True,
    )


class AIResourceRelevantLink(SQLModel, table=True):  # type: ignore [call-arg]
    __tablename__ = "ai_resource_relevant_link"
    parent_identifier: str = Field(
        max_length=IDENTIFIER_LENGTH,
        sa_column_args=[
            ForeignKey("ai_resource.identifier", onupdate="CASCADE", ondelete="CASCADE")
        ],
        sa_column_kwargs=dict(nullable=True, index=True),
        primary_key=True,
    )
    relevant_identifier: str = Field(
        max_length=IDENTIFIER_LENGTH,
        sa_column_args=[
            ForeignKey("ai_resource.identifier", onupdate="CASCADE", ondelete="CASCADE")
        ],
        sa_column_kwargs=dict(nullable=True, index=True),
        primary_key=True,
    )


class AIResourceORM(SQLModel, table=True):  # type: ignore [call-arg]
    __tablename__ = "ai_resource"
    identifier: str = Field(
        default_factory=create_id_generator(), max_length=IDENTIFIER_LENGTH, primary_key=True
    )
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
