"""
Utility functions for initializing the database and tables through SQLAlchemy.
"""
import itertools
from typing import List

from sqlalchemy import Engine, text, create_engine, select
from sqlalchemy.orm import Session

from connectors import DatasetConnector, PublicationConnector, CodeArtifactConnector
from .models import Base, DatasetDescription, Publication


def connect_to_database(
    url: str = "mysql://root:ok@127.0.0.1:3307/aiod",
    create_if_not_exists: bool = True,
    delete_first: bool = False,
) -> Engine:
    """Connect to server, optionally creating the database if it does not exist.

    Params
    ------
    url: URL to the database, see https://docs.sqlalchemy.org/en/20/core/engines.html#backend-specific-urls # noqa
    create_if_not_exists: create the database if it does not exist
    delete_first: drop the database before creating it again, to start with an empty database.
        IMPORTANT: Using `delete_first` means ALL data in that database will be lost permanently.

    Returns
    -------
    engine: Engine SQLAlchemy Engine configured with a database connection
    """

    if delete_first or create_if_not_exists:
        drop_or_create_database(url, delete_first)
    engine = create_engine(url, echo=True, pool_recycle=3600)

    with engine.connect() as connection:
        Base.metadata.create_all(connection, checkfirst=True)
        connection.commit()
    return engine


def drop_or_create_database(url: str, delete_first: bool):
    server, database = url.rsplit("/", 1)
    engine = create_engine(server, echo=True)  # Temporary engine, not connected to a database

    with engine.connect() as connection:
        if delete_first:
            connection.execute(text(f"DROP DATABASE IF EXISTS {database}"))
        connection.execute(text(f"CREATE DATABASE IF NOT EXISTS {database}"))
        connection.commit()
    engine.dispose()


def populate_database(
    engine: Engine,
    only_if_empty: bool = True,
    dataset_connectors: List[DatasetConnector] | None = None,
    publications_connectors: List[PublicationConnector] | None = None,
    codeartifact_connectors: List[CodeArtifactConnector] | None = None,
    limit_datasets: int | None = None,
    limit_publications: int | None = None,
    limit_codeartifacts: int | None = None,
):
    """Add some data to the Dataset and Publication tables."""

    if dataset_connectors is None:
        datasets_iterable = iter(())
    else:
        datasets_iterable = itertools.chain(
            *[c.fetch_all(limit=limit_datasets) for c in dataset_connectors]
        )
    if publications_connectors is None:
        publications_iterable = iter(())
    else:
        publications_iterable = itertools.chain(
            *[c.fetch_all(limit=limit_publications) for c in publications_connectors]
        )

    if codeartifact_connectors is None:
        codeartifact_iterable = iter(())
    else:
        codeartifact_iterable = itertools.chain(
            *[c.fetch_all(limit=limit_codeartifacts) for c in codeartifact_connectors]
        )

    datasets = list(datasets_iterable)
    publications = list(publications_iterable)
    codeartifacts = list(codeartifact_iterable)
    # For now, we cannot make use of generators, because we have to link the datasets with the
    # publications. This is a temporary setup though, so it makes sense to let the fetch_all()
    # return an iterator for future benefits.
    _link_datasets_with_publications(datasets, publications)
    with Session(engine) as session:
        data_exists = (
            session.scalars(select(Publication)).first()
            or session.scalars(select(DatasetDescription)).first()
        )
        if only_if_empty and data_exists:
            return

        session.add_all(datasets)
        session.add_all(publications)
        session.add_all(codeartifacts)
        session.commit()


def _link_datasets_with_publications(datasets, publications):
    """Linking some publications with some datasets. Temporary function to show the
    possibilities."""
    # fmt: off
    benchmark_dataset_ids = [
        181, 1111, 1596, 1457, 40981, 40983, 23517, 1489, 31, 40982, 41138, 41163, 41164, 41143,
        1169, 41167, 41147, 41158, 1487, 54, 41144, 41145, 41156, 41157, 41168, 4541, 1515, 188,
        1464, 1494, 1468, 1049, 23, 40975, 12, 1067, 40984, 40670, 3, 40978, 4134, 40701, 1475,
        4538, 4534, 41146, 41142, 40498, 40900, 40996, 40668, 4135, 1486, 41027, 1461, 1590, 41169,
        41166, 41165, 40685, 41159, 41161, 41150, 41162, 42733, 42734, 42732, 42746, 42742, 42769,
        43072
    ]
    # fmt: on
    benchmark_datasets = [
        d
        for d in datasets
        if d.node == "openml" and int(d.node_specific_identifier) in benchmark_dataset_ids
    ]
    benchmark_publications = [p for p in publications if p.title == "AMLB: an AutoML Benchmark"]
    higgs_title = "Searching for exotic particles in high-energy physics with deep learning"
    higgs_publication = [p for p in publications if p.title == higgs_title]
    for publication in higgs_publication:
        publication.datasets = [d for d in datasets if d.node == "openml" and d.name == "Higgs"]
    for publication in benchmark_publications:
        publication.datasets = benchmark_datasets
    return datasets, publications
