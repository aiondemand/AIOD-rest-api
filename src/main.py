"""
Defines Rest API endpoints.

Note: order matters for overloaded paths
(https://fastapi.tiangolo.com/tutorial/path-params/#order-matters).
"""
import argparse
import tomllib
import traceback
from typing import Dict

import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy import select, Engine, and_, delete, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import connectors
import schemas
from connectors import NodeName
from database.models import CodeArtifactDescription, DatasetDescription, Publication
from database.setup import connect_to_database, populate_database


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Please refer to the README.")
    parser.add_argument("--url-prefix", default="", help="Prefix for the api url.")
    parser.add_argument(
        "--rebuild-db",
        default="only-if-empty",
        choices=["no", "only-if-empty", "always"],
        help="Determines if the database is recreated.",
    )
    parser.add_argument(
        "--populate-datasets",
        default=[],
        nargs="+",
        choices=[p.name for p in NodeName],
        help="Zero, one or more nodes with which the datasets should get populated.",
    )
    parser.add_argument(
        "--populate-publications",
        default=[],
        nargs="+",
        choices=[p.name for p in NodeName],
        help="Zero, one or more nodes with which the publications should get populated.",
    )
    parser.add_argument(
        "--limit-number-of-datasets",
        type=int,
        default=None,
        help="Limit the number of initial datasets with which the database is populated, per node.",
    )
    parser.add_argument(
        "--limit-number-of-publications",
        default=None,
        type=int,
        help="Limit the number of initial publication with which the database is populated, "
        "per node.",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Use `--reload` for FastAPI.",
    )
    return parser.parse_args()


def _engine(rebuild_db: str) -> Engine:
    """
    Return a SqlAlchemy engine, backed by the MySql connection as configured in the configuration
    file.
    """
    with open("config.toml", "rb") as fh:
        config = tomllib.load(fh)
    db_config = config.get("database", {})
    username = db_config.get("name", "root")
    password = db_config.get("password", "ok")
    host = db_config.get("host", "demodb")
    port = db_config.get("port", 3306)
    database = db_config.get("database", "aiod")

    db_url = f"mysql://{username}:{password}@{host}:{port}/{database}"

    delete_before_create = rebuild_db == "always"
    return connect_to_database(db_url, delete_first=delete_before_create)


def _connector_from_node_name(connector_type: str, connector_dict: Dict, node_name: str):
    """Get the connector from the connector_dict, identified by its node name."""
    try:
        node = NodeName(node_name)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Node '{node_name}' not recognized.")
    connector = connector_dict.get(node, None)
    if connector is None:
        possibilities = ", ".join(f"`{c}`" for c in connectors.dataset_connectors.keys())
        msg = (
            f"No {connector_type} connector for node '{node_name}' available. Possible values:"
            f" {possibilities}"
        )
        raise HTTPException(status_code=501, detail=msg)
    return connector


def _retrieve_dataset(session, identifier, node=None) -> DatasetDescription:
    if node is None:
        query = select(DatasetDescription).where(DatasetDescription.id == identifier)
    else:
        query = select(DatasetDescription).where(
            and_(
                DatasetDescription.node_specific_identifier == identifier,
                DatasetDescription.node == node,
            )
        )
    dataset = session.scalars(query).first()
    if not dataset:
        if node is None:
            msg = f"Dataset '{identifier}' not found in the database."
        else:
            msg = f"Dataset '{identifier}' of '{node}' not found in the database."
        raise HTTPException(status_code=404, detail=msg)
    return dataset


def _retrieve_publication(session, identifier) -> Publication:
    query = select(Publication).where(Publication.id == identifier)
    publication = session.scalars(query).first()
    if not publication:
        raise HTTPException(
            status_code=404,
            detail=f"Publication '{identifier}' not found in the database.",
        )
    return publication

def _retrieve_codeartifact(session, identifier) -> CodeArtifactDescription:
    query = select(CodeArtifactDescription).where(CodeArtifactDescription.id == identifier)
    codeartifact = session.scalars(query).first()
    if not codeartifact:
        raise HTTPException(
            status_code=404,
            detail=f"CodeArtifact '{identifier}' not found in the database.",
        )
    return codeartifact



def _wrap_as_http_exception(exception: Exception) -> HTTPException:
    if isinstance(exception, HTTPException):
        return exception

    # This is an unexpected error. A mistake on our part. End users should not be informed about
    # details of problems they are not expected to fix, so we give a generic response and log the
    # error.
    traceback.print_exc()
    return HTTPException(
        status_code=500,
        detail=(
            "Unexpected exception while processing your request. Please contact the maintainers."
        ),
    )


def add_routes(app: FastAPI, engine: Engine, url_prefix=""):
    """Add routes to the FastAPI application"""

    @app.get(url_prefix + "/", response_class=HTMLResponse)
    def home() -> str:
        """Provides a redirect page to the docs."""
        return """
        <!DOCTYPE html>
        <html>
          <head>
            <meta http-equiv="refresh" content="0; url='docs'" />
          </head>
          <body>
            <p>The REST API documentation is <a href="docs">here</a>.</p>
          </body>
        </html>
        """

    # Multiple endpoints share the same set of parameters, we define a class for easy re-use of
    # dependencies:
    # https://fastapi.tiangolo.com/tutorial/dependencies/classes-as-dependencies/?h=depends#classes-as-dependencies # noqa
    class Pagination(BaseModel):
        offset: int = 0
        limit: int = 100

    @app.get(url_prefix + "/datasets/")
    def list_datasets(
        pagination: Pagination = Depends(Pagination),
    ) -> list[dict]:
        """Lists all datasets registered with AIoD.

        Query Parameter
        ------
         * nodes, list[str], optional: if provided, list only datasets from the given node.
        """
        # For additional information on querying through SQLAlchemy's ORM:
        # https://docs.sqlalchemy.org/en/20/orm/queryguide/index.html
        try:
            with Session(engine) as session:
                query = select(DatasetDescription).offset(pagination.offset).limit(pagination.limit)
                return [dataset.to_dict(depth=0) for dataset in session.scalars(query).all()]
        except Exception as e:
            raise _wrap_as_http_exception(e)

    @app.get(url_prefix + "/datasets/{identifier}")
    def get_dataset(identifier: str) -> dict:
        """Retrieve all meta-data for a specific dataset."""
        try:
            with Session(engine) as session:
                dataset = _retrieve_dataset(session, identifier)
            node = dataset.node
            connector = connectors.dataset_connectors.get(node, None)
            if connector is None:
                raise HTTPException(
                    status_code=501,
                    detail=f"No connector for node '{node}' available.",
                )
            dataset_meta = connector.fetch(dataset)
            return dataset_meta.dict()
        except Exception as e:
            raise _wrap_as_http_exception(e)

    @app.get(url_prefix + "/nodes")
    def get_nodes() -> list:
        """Retrieve information about all known nodes"""
        return list(NodeName)

    @app.get(url_prefix + "/nodes/{node}/datasets")
    def get_node_datasets(node: str, pagination: Pagination = Depends(Pagination)) -> list[dict]:
        """Retrieve all meta-data of the datasets of a single node."""
        try:
            with Session(engine) as session:
                query = (
                    select(DatasetDescription)
                    .where(DatasetDescription.node == node)
                    .offset(pagination.offset)
                    .limit(pagination.limit)
                )
                return [dataset.to_dict(depth=0) for dataset in session.scalars(query).all()]
        except Exception as e:
            raise _wrap_as_http_exception(e)

    @app.get(url_prefix + "/nodes/{node}/datasets/{identifier}")
    def get_node_dataset(node: str, identifier: str) -> dict:
        """Retrieve all meta-data for a specific dataset identified by the
        node-specific-identifier."""
        try:
            connector = _connector_from_node_name("dataset", connectors.dataset_connectors, node)
            with Session(engine) as session:
                dataset = _retrieve_dataset(session, identifier, node)
            dataset_meta = connector.fetch(dataset)
            return dataset_meta.dict()
        except Exception as e:
            raise _wrap_as_http_exception(e)

    @app.post(url_prefix + "/datasets/")
    def register_dataset(dataset: schemas.Dataset) -> dict:
        """Register a dataset with AIoD."""
        try:
            with Session(engine) as session:
                new_dataset = DatasetDescription(
                    name=dataset.name,
                    node=dataset.node,
                    node_specific_identifier=dataset.node_specific_identifier,
                )
                session.add(new_dataset)
                try:
                    session.commit()
                except IntegrityError:
                    session.rollback()
                    query = select(DatasetDescription).where(
                        and_(
                            DatasetDescription.node == dataset.node,
                            DatasetDescription.name == dataset.name,
                        )
                    )
                    existing_dataset = session.scalars(query).first()
                    raise HTTPException(
                        status_code=409,
                        detail="There already exists a dataset with the same "
                        f"node and name, with id={existing_dataset.id}.",
                    )
                return new_dataset.to_dict(depth=1)
        except Exception as e:
            raise _wrap_as_http_exception(e)

    @app.put(url_prefix + "/datasets/{identifier}")
    def put_dataset(identifier: str, dataset: schemas.Dataset) -> dict:
        """Update an existing dataset."""
        try:
            with Session(engine) as session:
                _retrieve_dataset(session, identifier)  # Raise error if dataset does not exist
                statement = (
                    update(DatasetDescription)
                    .values(
                        node=dataset.node,
                        name=dataset.name,
                        node_specific_identifier=dataset.node_specific_identifier,
                    )
                    .where(DatasetDescription.id == identifier)
                )
                session.execute(statement)
                session.commit()
                return _retrieve_dataset(session, identifier).to_dict(depth=1)
        except Exception as e:
            raise _wrap_as_http_exception(e)

    @app.delete(url_prefix + "/datasets/{identifier}")
    def delete_dataset(identifier: str):
        try:
            with Session(engine) as session:
                _retrieve_dataset(session, identifier)  # Raise error if it does not exist

                statement = delete(DatasetDescription).where(DatasetDescription.id == identifier)
                session.execute(statement)
                session.commit()
        except Exception as e:
            raise _wrap_as_http_exception(e)

    @app.get(url_prefix + "/publications")
    def list_publications(pagination: Pagination = Depends(Pagination)) -> list[dict]:
        """Lists all publications registered with AIoD."""
        try:
            with Session(engine) as session:
                return [
                    publication.to_dict(depth=0)
                    for publication in session.scalars(
                        select(Publication).offset(pagination.offset).limit(pagination.limit)
                    ).all()
                ]
        except Exception as e:
            raise _wrap_as_http_exception(e)

    @app.post(url_prefix + "/publications")
    def register_publication(publication: schemas.Publication) -> dict:
        """Add a publication."""
        try:
            with Session(engine) as session:
                new_publication = Publication(title=publication.title, url=publication.url)
                session.add(new_publication)
                session.commit()
                return new_publication.to_dict(depth=1)
        except Exception as e:
            raise _wrap_as_http_exception(e)

    @app.get(url_prefix + "/publications/{identifier}")
    def get_publication(identifier: str) -> dict:
        """Retrieves all information for a specific publication registered with AIoD."""
        try:
            with Session(engine) as session:
                publication = _retrieve_publication(session, identifier)
                return publication.to_dict(depth=1)
        except Exception as e:
            raise _wrap_as_http_exception(e)

    @app.put(url_prefix + "/publications/{identifier}")
    def update_publication(identifier: str, publication: schemas.Publication) -> dict:
        """Update this publication"""
        try:
            with Session(engine) as session:
                _retrieve_publication(session, identifier)  # Raise error if dataset does not exist
                statement = (
                    update(Publication)
                    .values(
                        title=publication.title,
                        url=publication.url,
                    )
                    .where(Publication.id == identifier)
                )
                session.execute(statement)
                session.commit()
                return _retrieve_publication(session, identifier).to_dict(depth=1)
        except Exception as e:
            raise _wrap_as_http_exception(e)

    @app.delete(url_prefix + "/publications/{identifier}")
    def delete_publication(identifier: str):
        """Delete this publication from AIoD."""
        try:
            with Session(engine) as session:
                _retrieve_publication(session, identifier)  # Raise error if it does not exist

                statement = delete(Publication).where(Publication.id == identifier)
                session.execute(statement)
                session.commit()
        except Exception as e:
            raise _wrap_as_http_exception(e)

    @app.get(url_prefix + "/datasets/{identifier}/publications")
    def list_publications_related_to_dataset(identifier: str) -> list[dict]:
        """Lists all publications registered with AIoD that use this dataset."""
        try:
            with Session(engine) as session:
                dataset = _retrieve_dataset(session, identifier)
                return [publication.to_dict(depth=0) for publication in dataset.publications]
        except Exception as e:
            raise _wrap_as_http_exception(e)

    @app.post(url_prefix + "/datasets/{dataset_id}/publications/{publication_id}")
    def relate_publication_to_dataset(dataset_id: str, publication_id: str):
        try:
            with Session(engine) as session:
                dataset = _retrieve_dataset(session, dataset_id)
                publication = _retrieve_publication(session, publication_id)
                if publication in dataset.publications:
                    raise HTTPException(
                        status_code=409,
                        detail=f"Dataset {dataset_id} is already linked to publication "
                        f"{publication_id}.",
                    )
                dataset.publications.append(publication)
                session.commit()
        except Exception as e:
            raise _wrap_as_http_exception(e)

    @app.delete(url_prefix + "/datasets/{dataset_id}/publications/{publication_id}")
    def delete_relation_publication_to_dataset(dataset_id: str, publication_id: str):
        try:
            with Session(engine) as session:
                dataset = _retrieve_dataset(session, dataset_id)
                publication = _retrieve_publication(session, publication_id)
                if publication not in dataset.publications:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Dataset {dataset_id} is not linked to publication "
                        f"{publication_id}.",
                    )
                dataset.publications = [p for p in dataset.publications if p != publication]
                session.commit()
        except Exception as e:
            raise _wrap_as_http_exception(e)


    @app.get(url_prefix + "/codeartifacts/{identifier}")
    def get_codeartifact(identifier: str) -> dict:
        """Retrieves all information for a specific codeartifact registered with AIoD."""
        try:
            with Session(engine) as session:
                codeartifact = _retrieve_codeartifact(session, identifier)
                return codeartifact
        except Exception as e:
            raise _wrap_as_http_exception(e)


def create_app() -> FastAPI:
    """Create the FastAPI application, complete with routes."""
    app = FastAPI()
    args = _parse_args()

    dataset_connectors = [
        _connector_from_node_name("dataset", connectors.dataset_connectors, node_name)
        for node_name in args.populate_datasets
    ]
    publication_connectors = [
        _connector_from_node_name("publication", connectors.publication_connectors, node_name)
        for node_name in args.populate_publications
    ]
    engine = _engine(args.rebuild_db)
    if len(dataset_connectors) + len(publication_connectors) > 0:
        populate_database(
            engine,
            dataset_connectors=dataset_connectors,
            publications_connectors=publication_connectors,
            only_if_empty=True,
            limit_datasets=args.limit_number_of_datasets,
            limit_publications=args.limit_number_of_publications,
        )
    add_routes(app, engine, url_prefix=args.url_prefix)
    return app


def main():
    """Run the application. Placed in a separate function, to avoid having global variables"""
    args = _parse_args()
    uvicorn.run("main:create_app", host="0.0.0.0", reload=args.reload, factory=True)


if __name__ == "__main__":
    main()
