"""
Contains the definitions for the different tables in our database.
See also:
   * https://docs.sqlalchemy.org/en/20/orm/declarative_tables.html#using-annotated-declarative-table-type-annotated-forms-for-mapped-column # noqa
   * https://docs.sqlalchemy.org/en/20/orm/dataclasses.html#orm-declarative-native-dataclasses

Note: because we use MySQL in the demo, we need to explicitly set maximum string lengths.
"""
import typing  # noqa:F401 (flake8 raises incorrect 'Module imported but unused' error)
from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from database.model.base import Base
from database.model.dataset_relationships import (
    dataset_keyword_relationship,
    dataset_license_relationship,
)
from database.model.news_relationships import (
    news_keyword_relationship,
    news_business_category_relationship,
)
from database.model.educational_resource_relationships import (
    educational_resource_business_category_relationship,
    educational_resource_keyword_relationship,
    educational_resource_technical_category_relationship,
)

from database.model.organisation_relationships import (
    organisation_business_category_relationship,
    organisation_technical_category_relationship,
)


from database.model.publication_relationships import (
    publication_license_relationship,
    publication_resource_type_relationship,
)


from database.model.project_relationships import project_keyword_relationship
from database.model.event_relationships import event_business_category_relationship

from database.model.unique_model import UniqueMixin

if TYPE_CHECKING:  # avoid circular imports; only import while type checking
    from database.model.dataset import OrmDataset
    from database.model.news import OrmNews
    from database.model.educational_resource import OrmEducationalResource
    from database.model.event import OrmEvent
    from database.model.organisation import OrmOrganisation
    from database.model.project import OrmProject
    from database.model.publication import OrmPublication


class OrmLicense(UniqueMixin, Base):
    """
    A license document, indicated by URL.

    For now only related to datasets, but we can extend it with relationships to other resources.
    """

    @classmethod
    def _unique_hash(cls, name):
        return name

    @classmethod
    def _unique_filter(cls, query, name):
        return query.filter(cls.name == name)

    __tablename__ = "licenses"
    identifier: Mapped[int] = mapped_column(init=False, primary_key=True)
    name: Mapped[str] = mapped_column(String(150), unique=True)
    datasets: Mapped[list["OrmDataset"]] = relationship(
        default_factory=list, back_populates="license", secondary=dataset_license_relationship
    )
    publications: Mapped[list["OrmPublication"]] = relationship(
        default_factory=list, back_populates="license", secondary=publication_license_relationship
    )


class OrmResourcetype(UniqueMixin, Base):
    """
    A resorce type

    For now only related to publications, it can be extended with relationships to other resources.
    """

    @classmethod
    def _unique_hash(cls, name):
        return name

    @classmethod
    def _unique_filter(cls, query, name):
        return query.filter(cls.name == name)

    __tablename__ = "resource_types"
    identifier: Mapped[int] = mapped_column(init=False, primary_key=True)
    name: Mapped[str] = mapped_column(String(150), unique=True)
    publications: Mapped[list["OrmPublication"]] = relationship(
        default_factory=list,
        back_populates="resource_type",
        secondary=publication_resource_type_relationship,
    )


class OrmKeyword(UniqueMixin, Base):
    """
    Keywords or tags used to describe some item

    For now only related to datasets and news, but we can extend it with relationships to other
    resources.
    """

    @classmethod
    def _unique_hash(cls, name):
        return name

    @classmethod
    def _unique_filter(cls, query, name):
        return query.filter(cls.name == name)

    __tablename__ = "keywords"
    identifier: Mapped[int] = mapped_column(init=False, primary_key=True)
    name: Mapped[str] = mapped_column(String(150), unique=True)
    datasets: Mapped[list["OrmDataset"]] = relationship(
        default_factory=list, back_populates="keywords", secondary=dataset_keyword_relationship
    )
    news: Mapped[list["OrmNews"]] = relationship(
        default_factory=list, back_populates="keywords", secondary=news_keyword_relationship
    )
    educational_resources: Mapped[list["OrmEducationalResource"]] = relationship(
        default_factory=list,
        back_populates="keywords",
        secondary=educational_resource_keyword_relationship,
    )
    projects: Mapped[list["OrmProject"]] = relationship(
        default_factory=list, back_populates="keywords", secondary=project_keyword_relationship
    )


class OrmBusinessCategory(UniqueMixin, Base):
    """Any business category"""

    @classmethod
    def _unique_hash(cls, category):
        return category

    @classmethod
    def _unique_filter(cls, query, category):
        return query.filter(cls.category == category)

    __tablename__ = "business_categories"

    identifier: Mapped[int] = mapped_column(init=False, primary_key=True)
    category: Mapped[str] = mapped_column(String(250), unique=True)
    news: Mapped[list["OrmNews"]] = relationship(
        default_factory=list,
        back_populates="business_categories",
        secondary=news_business_category_relationship,
    )
    educational_resources: Mapped[list["OrmEducationalResource"]] = relationship(
        default_factory=list,
        back_populates="business_categories",
        secondary=educational_resource_business_category_relationship,
    )
    events: Mapped[list["OrmEvent"]] = relationship(
        default_factory=list,
        back_populates="business_categories",
        secondary=event_business_category_relationship,
    )

    organisations: Mapped[list["OrmOrganisation"]] = relationship(
        default_factory=list,
        back_populates="business_categories",
        secondary=organisation_business_category_relationship,
    )


class OrmTechnicalCategory(UniqueMixin, Base):
    """Any technical category"""

    @classmethod
    def _unique_hash(cls, category):
        return category

    @classmethod
    def _unique_filter(cls, query, category):
        return query.filter(cls.category == category)

    __tablename__ = "technical_categories"

    category: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    identifier: Mapped[int] = mapped_column(init=False, primary_key=True)

    educational_resources: Mapped[list["OrmEducationalResource"]] = relationship(
        default_factory=list,
        back_populates="technical_categories",
        secondary=educational_resource_technical_category_relationship,
    )

    organisations: Mapped[list["OrmOrganisation"]] = relationship(
        default_factory=list,
        back_populates="technical_categories",
        secondary=organisation_technical_category_relationship,
    )
