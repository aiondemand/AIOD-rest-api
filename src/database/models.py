"""
Contains the definitions for the different tables in our database.
See also:
   * https://docs.sqlalchemy.org/en/20/orm/declarative_tables.html#using-annotated-declarative-table-type-annotated-forms-for-mapped-column # noqa
   * https://docs.sqlalchemy.org/en/20/orm/dataclasses.html#orm-declarative-native-dataclasses

Note: because we use MySQL in the demo, we need to explicitly set maximum string lengths.
"""
import dataclasses
import typing  # noqa:F401 (flake8 raises incorrect 'Module imported but unused' error)

from sqlalchemy import ForeignKey, Table, Column, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, MappedAsDataclass, relationship


class Base(DeclarativeBase, MappedAsDataclass):
    """Maps subclasses to Python Dataclasses, providing e.g., `__init__` automatically."""

    def to_dict(self, depth: int = 1) -> dict:
        """
        Serializes all fields of the dataclasses, as well as its references, up to a certain
        depth.

        Whenever the attributes are themselves dataclasses, such as Datasets referencing
        Publications, these dataclasses may refer back to other dataclasses, possibly in a cyclic
        manner. For this reason, using dataclasses.to_dict(object) results in infinite recursion.
        To prevent this from happening, we define this method which only recurs a `depth` amount
        of time.

        Params
        ------
        depth, int (default=1): dictates how many levels of object references to jsonify.
          When maximum depth is reached, any further references will simply be omitted.
          E.g., for depth=1 a Dataset will include Publications in its JSON, but not the
          Publications' Datasets.
        """
        d = {}  # type: typing.Dict[str, typing.Any]
        for field in dataclasses.fields(self):
            value = getattr(self, field.name)
            if isinstance(value, Base):
                if depth > 0:
                    d[field.name] = value.to_dict(depth=depth - 1)
            elif isinstance(value, (list, set)):
                if all(isinstance(item, Base) for item in value):
                    if depth > 0:
                        d[field.name] = type(value)(item.to_dict(depth - 1) for item in value)
                elif not all(isinstance(item, type(next(iter(value)))) for item in value):
                    raise NotImplementedError("Serializing mixed-type lists is not supported.")
                else:
                    d[field.name] = value
            else:
                d[field.name] = value
        return d


dataset_publication_relationship = Table(
    "dataset_publication",
    Base.metadata,
    Column("publication_id", ForeignKey("publications.id")),
    Column("dataset_id", ForeignKey("datasets.id")),
)


class DatasetDescription(Base):
    """Keeps track of which dataset is stored where."""

    __tablename__ = "datasets"
    __table_args__ = (
        UniqueConstraint(
            "node",
            "node_specific_identifier",
            name="dataset_unique_node_node_specific_identifier",
        ),
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    node: Mapped[str] = mapped_column(String(30), nullable=False)
    node_specific_identifier: Mapped[str] = mapped_column(String(250), nullable=False)
    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    publications: Mapped[list["Publication"]] = relationship(
        default_factory=list,
        back_populates="datasets",
        secondary=dataset_publication_relationship,
    )


class Publication(Base):
    """Any publication."""

    __tablename__ = "publications"
    __table_args__ = (
        UniqueConstraint(
            "title",
            "url",
            name="publications_unique_title_url",
        ),
    )
    title: Mapped[str] = mapped_column(String(250), nullable=False)
    url: Mapped[str] = mapped_column(String(250), nullable=False)
    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    datasets: Mapped[list["DatasetDescription"]] = relationship(
        default_factory=list,
        back_populates="publications",
        secondary=dataset_publication_relationship,
    )


class CodeArtifactDescription(Base):
    """Any code artifact."""

    __tablename__ = "codeartifacts"
    __table_args__ = (
        UniqueConstraint(
            "node",
            "node_specific_identifier",
            name="publications_unique_node_node_specific_identifier",
        ),
    )
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    doi: Mapped[str] = mapped_column(String(250), nullable=False)
    node: Mapped[str] = mapped_column(String(30), nullable=False)
    node_specific_identifier: Mapped[str] = mapped_column(String(250), nullable=False)
    id: Mapped[int] = mapped_column(init=False, primary_key=True)
