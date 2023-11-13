#!python3
"""
Actual (hard) deletion of soft-deleted items.

We use soft-deletion for most resources, meaning that the .date_deleted attribute is set on a
delete request, rather than actual deletion. This module hard deletes those items that have been
soft deleted some time ago.
"""
import argparse
import datetime
from datetime import timedelta
from typing import Type

from sqlalchemy import delete, and_
from sqlalchemy.engine import Engine
from sqlalchemy.sql.operators import is_not
from sqlmodel import Session

from database.model.concept.concept import AIoDConcept
from database.model.helper_functions import non_abstract_subclasses
from database.setup import sqlmodel_engine


def hard_delete_older_than(engine: Engine, time_threshold: timedelta):
    classes: list[Type[AIoDConcept]] = non_abstract_subclasses(AIoDConcept)
    date_threshold = datetime.datetime.now() - time_threshold
    with Session(engine) as session:
        for concept in classes:
            filter_ = and_(
                is_not(concept.date_deleted, None),
                concept.date_deleted < date_threshold,  # type: ignore
            )
            statement = delete(concept).where(filter_)
            session.exec(statement)
            session.commit()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Hard delete all soft-deleted items of a certain age."
    )
    parser.add_argument(
        "--time-threshold-minutes",
        required=True,
        type=int,
        help="Delete all items that have been soft-deleted at least this long ago.",
    )
    return parser.parse_args()


def main():
    args = _parse_args()

    engine = sqlmodel_engine(rebuild_db="never")
    time_threshold = timedelta(minutes=args.time_threshold_minutes)
    hard_delete_older_than(engine=engine, time_threshold=time_threshold)


if __name__ == "__main__":
    main()
