from argparse import ArgumentParser
from pathlib import Path
from typing import NamedTuple

from sqlalchemy import select
from sqlmodel import Session

from database.model.named_relation import Taxonomy


def parse_args():
    parser = ArgumentParser()
    parser.add_argument(
        "--definitions-file",
        type=Path,
    )
    parser.add_argument(
        "--taxonomy",
        type=str,
        help="The taxonomy to update, e.g. 'industrial sector. Must match <database or file?>",
    )


class Term(NamedTuple):
    term: str
    definition: str


def synchronize(
    taxonomy_type: type[Taxonomy],
    definitions: list[Term],
    session: Session,
) -> None:
    """Update the taxonomy table to reflect the provided definitions.

    - adds new definitions to the table
    - updates descriptions of definitions
    - mark definitions no longer included as unofficial
    """
    db_definitions = {term.name: term for term in session.scalars(select(taxonomy_type)).all()}
    for term_object in db_definitions.values():
        term_object.official = False

    for term, definition in definitions:
        if term_object := db_definitions.get(term):
            term_object.definition = definition
            term_object.official = True
        else:
            term_object = taxonomy_type(name=term, definition=definition, official=True)
            session.add(term_object)

    session.commit()


def main():
    pass


if __name__ == "__main__":
    main()
