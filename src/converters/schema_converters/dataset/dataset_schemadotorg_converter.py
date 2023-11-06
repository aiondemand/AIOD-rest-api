from typing import Type, TypeVar

from sqlmodel import select, Session

from converters.schema.schema_dot_org import (
    SchemaDotOrgDataset,
    SchemaDotOrgOrganization,
    SchemaDotOrgPerson,
    SchemaDotOrgDataDownload,
)
from converters.schema_converters.schema_converter import SchemaConverter
from database.model.agent.agent_table import AgentTable
from database.model.agent.organisation import Organisation
from database.model.agent.person import Person
from database.model.dataset.dataset import Dataset
from database.model.knowledge_asset.publication import Publication


class DatasetConverterSchemaDotOrg(SchemaConverter[Dataset, SchemaDotOrgDataset]):
    """
    Convert an AIoD Dataset into a schema.org json-ld representation.
    """

    @property
    def to_class(self) -> Type[SchemaDotOrgDataset]:
        return SchemaDotOrgDataset

    def convert(self, session: Session, aiod: Dataset) -> SchemaDotOrgDataset:
        creator = [_person(creator) for creator in aiod.creator]
        funder = [_agent(session, agent_table) for agent_table in aiod.funder]
        citations = [_publication(publication) for publication in aiod.citation]

        return SchemaDotOrgDataset(
            description=aiod.description,
            identifier=aiod.identifier,
            name=aiod.name,
            alternateName=_list_to_one_or_none([a.name for a in aiod.alternate_name]),
            citation=_list_to_one_or_none(citations),
            creator=_list_to_one_or_none(creator),
            dateModified=aiod.aiod_entry.date_modified,
            datePublished=aiod.date_published,
            isAccessibleForFree=True,
            funder=_list_to_one_or_none(funder),
            keywords=_list_to_one_or_none([a.name for a in aiod.keyword]),
            sameAs=aiod.same_as,
            version=aiod.version,
            url=f"https://aiod.eu/api/datasets/{aiod.identifier}",  # TODO: update url
            distribution=_list_to_one_or_none(
                [
                    SchemaDotOrgDataDownload(
                        name=d.name,
                        description=d.description,
                        contentUrl=d.content_url,
                        contentSize=d.content_size_kb,
                        encodingFormat=d.encoding_format,
                    )
                    for d in aiod.distribution
                ]
            ),
            issn=aiod.issn,
            license=aiod.license.name if aiod.license is not None else None,
            measurementTechnique=aiod.measurement_technique,
            size=f"unit={aiod.size.unit} value={aiod.size.value}"
            if aiod.size is not None
            else None,
            temporalCoverage=aiod.temporal_coverage,
        )


V = TypeVar("V")


def _list_to_one_or_none(value: set[V] | list[V]) -> set[V] | list[V] | V | None:
    """All schema.org fields can be repeated. This function can be used to return None if the
    input is empty, return the only value if there is only one value, or otherwise return the
    input set/list.
    """
    if len(value) == 0:
        return None
    if len(value) == 1:
        (only,) = value
        return only
    return value


def _person(person: Person) -> SchemaDotOrgPerson:
    return SchemaDotOrgPerson(name=person.name)


def _organisation(organisation: Organisation) -> SchemaDotOrgOrganization:
    return SchemaDotOrgOrganization(name=organisation.name)


def _publication(publication: Publication) -> str:
    return f"{publication.name} by {', '.join(creator.name for creator in publication.creator)}"


def _agent(session: Session, agent: AgentTable) -> SchemaDotOrgPerson | SchemaDotOrgOrganization:
    if agent.type == Person.__tablename__:
        query = select(Person).where(Person.identifier == agent.identifier)
        person = session.scalars(query).first()
        return _person(person)
    if agent.type == Organisation.__tablename__:
        query = select(Organisation).where(Organisation.identifier == agent.identifier)
        organisation = session.scalars(query).first()
        return _organisation(organisation)
    raise ValueError(f"Agent type {agent.type} not recognized.")
