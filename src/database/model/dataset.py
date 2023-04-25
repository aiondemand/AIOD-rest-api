from datetime import datetime

from sqlalchemy import UniqueConstraint, String, DateTime, Boolean, and_
from sqlalchemy.orm import Mapped, mapped_column, relationship


from database.model.ai_resource import OrmAIResource
from database.model.dataset_relationships import (
    dataset_alternateName_relationship,
    dataset_distribution_relationship,
    dataset_dataset_relationship,
    dataset_keyword_relationship,
    dataset_license_relationship,
    dataset_publication_relationship,
    dataset_measuredValue_relationship,
)
from database.model.general import OrmKeyword, OrmLicense
from database.model.base import Base
from database.model.publication import OrmPublication
from database.model.unique_model import UniqueMixin
from sqlalchemy import ForeignKey


class OrmDataset(OrmAIResource):
    """Keeps track of which dataset is stored where."""

    __tablename__ = "datasets"
    __table_args__ = (
        UniqueConstraint(
            "name",
            "version",
            name="dataset_name_version_unique",
        ),
    )

    identifier: Mapped[int] = mapped_column(
        ForeignKey("ai_resources.identifier"), init=False, primary_key=True
    )
    # Defined on AIResource as well, but without this attribute here, SQLAlchemy does not
    # understand the self-referential relationship in has_part and is_part

    # Required fields
    description: Mapped[str] = mapped_column(String(5000), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    same_as: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)

    # Recommended fields
    creator: Mapped[str] = mapped_column(String(150), default=None, nullable=True)
    # TODO(issue 9): creator repeated organisation/person
    date_modified: Mapped[datetime] = mapped_column(DateTime, nullable=True, default=None)
    date_published: Mapped[datetime] = mapped_column(DateTime, nullable=True, default=None)
    funder: Mapped[str] = mapped_column(String(150), default=None, nullable=True)
    # TODO(issue 9): funder repeated organisation/person
    is_accessible_for_free: Mapped[bool] = mapped_column(Boolean, default=None, nullable=True)
    issn: Mapped[str] = mapped_column(String(8), default=None, nullable=True)
    size: Mapped[int] = mapped_column(default=None, nullable=True)
    spatial_coverage: Mapped[str] = mapped_column(String(500), default=None, nullable=True)
    temporal_coverage_from: Mapped[datetime] = mapped_column(DateTime, default=None, nullable=True)
    temporal_coverage_to: Mapped[datetime] = mapped_column(DateTime, default=None, nullable=True)
    version: Mapped[str] = mapped_column(String(150), default=None, nullable=True)

    # Relations
    license: Mapped["OrmLicense"] = relationship(
        back_populates="datasets", secondary=dataset_license_relationship, default=None
    )
    has_parts: Mapped[list["OrmDataset"]] = relationship(
        default_factory=list,
        back_populates="is_part",
        primaryjoin=dataset_dataset_relationship.c.parent_id == identifier,
        secondary=dataset_dataset_relationship,
        secondaryjoin=dataset_dataset_relationship.c.child_id == identifier,
    )
    is_part: Mapped[list["OrmDataset"]] = relationship(
        default_factory=list,
        back_populates="has_parts",
        primaryjoin=dataset_dataset_relationship.c.child_id == identifier,
        secondary=dataset_dataset_relationship,
        secondaryjoin=dataset_dataset_relationship.c.parent_id == identifier,
    )
    alternate_names: Mapped[list["OrmAlternateName"]] = relationship(
        default_factory=list,
        back_populates="datasets",
        secondary=dataset_alternateName_relationship,
    )
    citations: Mapped[list["OrmPublication"]] = relationship(
        default_factory=list,
        back_populates="datasets",
        secondary=dataset_publication_relationship,
    )
    distributions: Mapped[list["OrmDataDownload"]] = relationship(
        default_factory=list,
        back_populates="dataset",
        secondary=dataset_distribution_relationship,
    )
    keywords: Mapped[list["OrmKeyword"]] = relationship(
        default_factory=list,
        back_populates="datasets",
        secondary=dataset_keyword_relationship,
    )
    measured_values: Mapped[list["OrmMeasuredValue"]] = relationship(
        default_factory=list,
        back_populates="datasets",
        secondary=dataset_measuredValue_relationship,
    )

    __mapper_args__ = {
        "polymorphic_identity": "dataset",
        "inherit_condition": identifier == OrmAIResource.identifier,
    }


class OrmDataDownload(Base):
    """All or part of a Dataset in downloadable form"""

    __tablename__ = "data_downloads"
    identifier: Mapped[int] = mapped_column(init=False, primary_key=True)
    content_url: Mapped[str] = mapped_column(String(250), nullable=False, unique=True)
    content_size_kb: Mapped[int] = mapped_column(default=None, nullable=True)
    description: Mapped[str] = mapped_column(String(5000), default=None, nullable=True)
    encoding_format: Mapped[str] = mapped_column(String(255), default=None, nullable=True)
    name: Mapped[str] = mapped_column(String(150), default=None, nullable=True)
    dataset: Mapped["OrmDataset"] = relationship(
        back_populates="distributions", secondary=dataset_distribution_relationship, init=False
    )


class OrmMeasuredValue(UniqueMixin, Base):
    """The variable that this dataset measures. For example, temperature or pressure, including the
    technique, technology, or methodology used in a dataset"""

    @classmethod
    def _unique_hash(cls, variable, technique):
        return f"Variable:'{variable}'|Technique:'{technique}'"

    @classmethod
    def _unique_filter(cls, query, variable, technique):
        return query.filter(and_(cls.variable == variable, cls.technique == technique))

    __tablename__ = "measured_values"
    __table_args__ = (
        UniqueConstraint(
            "variable",
            "technique",
            name="measuredValue_variable_technique",
        ),
    )
    identifier: Mapped[int] = mapped_column(init=False, primary_key=True)
    variable: Mapped[str] = mapped_column(String(150))
    technique: Mapped[str] = mapped_column(String(150))
    datasets: Mapped[list["OrmDataset"]] = relationship(
        default_factory=list,
        back_populates="measured_values",
        secondary=dataset_measuredValue_relationship,
    )


class OrmAlternateName(UniqueMixin, Base):
    """
    An alias for a dataset

    Only related to datasets. If another resource needs an alias as well, we should
    probably define a new table.
    """

    @classmethod
    def _unique_hash(cls, name):
        return name

    @classmethod
    def _unique_filter(cls, query, name):
        return query.filter(cls.name == name)

    __tablename__ = "alternate_names"
    identifier: Mapped[int] = mapped_column(init=False, primary_key=True)
    name: Mapped[str] = mapped_column(String(150), unique=True)
    datasets: Mapped[list["OrmDataset"]] = relationship(
        default_factory=list,
        back_populates="alternate_names",
        secondary=dataset_alternateName_relationship,
    )
