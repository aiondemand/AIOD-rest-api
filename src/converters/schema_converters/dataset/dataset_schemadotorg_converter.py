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
        creator = [
            SchemaDotOrgPerson(name=creator.contact_name)
            for creator in aiod.creator
            if creator.contact_name
        ]
        funder = [_agent(session, agent_table) for agent_table in aiod.funder]
        funder = [f for f in funder if f]
        citations = [_publication(publication) for publication in aiod.citation]
        if aiod.description and aiod.description.plain:
            description = aiod.description.plain
        elif aiod.description and aiod.description.html:
            description = aiod.description.html
        else:
            description = None
        return SchemaDotOrgDataset(
            description=description,
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


def _publication(publication: Publication) -> str:
    names = (creator.contact_name for creator in publication.creator if creator.contact_name)
    return f"{publication.name} by {', '.join(names)}"


def _agent(
    session: Session, agent: AgentTable
) -> SchemaDotOrgPerson | SchemaDotOrgOrganization | None:
    if agent.type == Person.__tablename__:
        query = select(Person).where(Person.agent_id == agent.identifier)
        person: Person = session.scalars(query).first()
        if person:
            name = ", ".join([name for name in (person.surname, person.given_name) if name])
            name = name if name else person.name
            if name:
                return SchemaDotOrgPerson(name=person.name)
    elif agent.type == Organisation.__tablename__:
        query = select(Organisation).where(Organisation.agent_id == agent.identifier)
        organisation: Organisation = session.scalars(query).first()
        name = organisation.legal_name if organisation.legal_name else organisation.name
        if name:
            return SchemaDotOrgOrganization(name=name)
    else:
        raise ValueError(f"Agent type {agent.type} not recognized.")
    return None
