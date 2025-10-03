from __future__ import annotations
import json
from argparse import ArgumentParser
from pathlib import Path
from typing import NamedTuple
import logging

from sqlalchemy import select
from sqlmodel import Session

from database.model.named_relation import Taxonomy
from database.model.knowledge_asset.PublicationType import PublicationType
from database.model.ai_resource.research_area import ResearchArea
from database.session import DbSession
from database.model.ai_asset.license import License
from database.model.ai_resource.industrial_sector import IndustrialSector
from database.model.ai_resource.scientific_domain import ScientificDomain
from database.model.news.news_category import NewsCategory
from database.model.agent.organisation import (
    NumberOfEmployees,
    Turnover,
    OrganisationType,
    OrganisationActivityType,
)
from database.model.event.event import EventStatus, EventMode
from database.model.agent.language import Language
from database.model.educational_resource.educational_resource import EducationalLevel
from database.model.educational_resource.educational_resource import (
    LearningMode,
    EducationalCompetency,
)
from database.model.agent.location import Country


def parse_args():
    parser = ArgumentParser()
    parser.add_argument(
        "--definitions-file",
        type=Path,
        default=Path("/data/taxonomies.json"),
    )
    return parser.parse_args()


class Term(NamedTuple):
    name: str
    definition: str
    children: list[Term]


type_by_name: dict[str, type] = {
    "Publication": PublicationType,
    "Research Area": ResearchArea,
    "Business Sector": IndustrialSector,
    "Licence": License,
    "News Category": NewsCategory,
    "Scientific Domain": ScientificDomain,
    "Number of Employees": NumberOfEmployees,
    "Turnover": Turnover,
    "Organisation Type": OrganisationType,
    "Event Status": EventStatus,
    "Event Mode": EventMode,
    "Language": Language,
    "Educational Level": EducationalLevel,
    "Learning Mode": LearningMode,
    "Educational Competency": EducationalCompetency,
    "Organisation Activity Type": OrganisationActivityType,
    "Country": Country,
}


def load_taxonomies_from_json(file_path: Path):
    with file_path.open("r") as fh:
        file_content = json.load(fh)

    taxonomies = file_content["aiod_taxonomies"]
    for taxonomy in taxonomies:
        name = taxonomy["taxonomy_name"]
        if (type_ := type_by_name.get(name)) is None:
            logging.info(f"Skipping synchronization of {name!r}.")
            continue  # not implemented in the catalogue yet
        logging.info(f"Loading definitions for {name!r}.")

        def create_term(element: dict) -> Taxonomy:
            term = element["label"]["value"]
            if len(term) > 256:
                raise ValueError(f"Term {term!r} exceeds maximum length of 256 characters.")
            definition = element["definition"]
            if len(definition) > 1800:
                definition_too_long = f"Definition for {term!r} exceeds maximum of 1800 characters."
                raise ValueError(definition_too_long)
            return type_(  # type: ignore[misc]
                name=term,
                definition=definition,
                official=True,
                children=[create_term(e) for e in element["elements"]],
            )

        definitions = [create_term(item) for item in taxonomy["elements"]]
        yield type_, definitions


def synchronize(
    taxonomy_type: type[Taxonomy],  # Really the subclass type, e.g. ResearchArea
    definitions: list[Taxonomy],  # Same
    session: Session,
) -> None:
    """Update the taxonomy table to reflect the provided definitions.

    - adds new definitions to the table
    - updates descriptions of definitions
    - mark definitions no longer included as unofficial
    """
    logging.info(f"Updating {taxonomy_type.__tablename__!r}")
    # We first invalidate everything, so only what is still in the file will remain 'official'
    db_definitions = {
        term.name.casefold(): term
        for term in session.scalars(select(taxonomy_type)).all()
        if term.name  # Due to migrations there may be one term which is null, but this is never in the json
    }
    added_terms = dict()
    for term_object in db_definitions.values():
        term_object.official = False

    def synchronize_term(term: Taxonomy):
        synchronized_children = [synchronize_term(child) for child in term.children]

        if term_object := db_definitions.get(term.name.casefold()):
            logging.debug(f"Updating term {term.name!r}")
            term_object.name = term.name  # The name might change in capitalization
            term_object.definition = term.definition
            term_object.official = True
            term_object.children = synchronized_children
            return term_object

        if term.name not in added_terms:
            logging.debug(f"Adding new term {term.name!r}")
            if term.parent is not None and (
                parent := db_definitions.get(term.parent.name.casefold())
            ):
                term.parent = parent
            term.children = synchronized_children
            added_terms[term.name] = term
            return term

        logging.warning(f"Term {term.name!r} defined more than once!")
        return None

    for term in definitions:
        sync_term = synchronize_term(term)
        if sync_term is not None:
            session.merge(sync_term)


def synchronize_taxonomy_from_file(file: Path) -> None:
    taxonomies = load_taxonomies_from_json(file)
    with DbSession(autoflush=False) as session:
        for type_, definitions in taxonomies:
            synchronize(type_, definitions, session)
        logging.info("Committing changes to database.")
        session.commit()


def main():
    logging.basicConfig(level=logging.INFO)
    logging.info("Starting synchronization script.")
    args = parse_args()
    synchronize_taxonomy_from_file(args.definitions_file)


if __name__ == "__main__":
    main()
