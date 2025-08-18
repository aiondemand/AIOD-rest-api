import argparse
import importlib
import json
import logging
import pathlib
import sys
from datetime import datetime
from typing import Optional

from sqlmodel import select, Session

from connectors.abstract.resource_connector import ResourceConnector, RESOURCE
from connectors.record_error import RecordError
from connectors.resource_with_relations import ResourceWithRelations
from database.model.concept.aiod_entry import EntryStatus
from database.model.concept.concept import AIoDConcept
from database.model.platform.platform_names import PlatformName
from database.session import DbSession
from database.setup import _get_existing_resource
from routers import ResourceRouter, resource_routers, enum_routers
from setup_logger import setup_logger
from versioning import Version

RELATIVE_PATH_STATE_JSON = pathlib.Path("state.json")
RELATIVE_PATH_ERROR_CSV = pathlib.Path("errors.csv")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Synchronize a resource from a platform to the AIoD database."
    )
    parser.add_argument(
        "-c",
        "--connector",
        required=True,
        help="The connector to use. Please provide a relative path such as "
        "'connectors.zenodo.zenodo_dataset_connector.ZenodoDatasetConnector' where the "
        "last part is the class name.",
    )
    parser.add_argument(
        "-w",
        "--working-dir",
        required=True,
        help="The working directory. The status will be stored here, next to the logs and a "
        "list of failed resources",
    )
    parser.add_argument(
        "-rm",
        "--remove_state",
        action=argparse.BooleanOptionalAction,
        help="Remove the existing state files (the files in the working directory) on startup (so "
        "to start with a clean sheet). This is only meant for development, not for "
        "production!",
    )
    parser.add_argument(
        "--from-date",
        type=lambda d: datetime.strptime(d, "%Y-%m-%d"),
        help="The start date. Only relevant for the first run of date-based connectors. "
        "In subsequent runs, date-based connectors will synchronize from the previous "
        "end-time. Format: YYYY-MM-DD",
    )
    parser.add_argument(
        "--from-identifier",
        type=int,
        help="The start identifier. Only relevant for the first run of identifier-based "
        "connectors. In subsequent runs, identifier-based connectors will "
        "synchronize from the previous end-identifier.",
    )
    parser.add_argument(
        "-l",
        "--limit",
        type=int,
        help="Implemented by some connectors for testing purposes: limit the number of results.",
    )
    parser.add_argument(
        "--save-every",
        type=int,
        help="Save the state file every N records. In case the complete program is killed, "
        "you can then resume the next run from the last saved state.",
    )
    return parser.parse_args()


def exception_handler(exc_type, exc_value, exc_traceback):
    logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))


def save_to_database(
    session: Session,
    connector: ResourceConnector,
    router: ResourceRouter,
    item: RESOURCE | ResourceWithRelations[RESOURCE] | RecordError,
    user,
) -> Optional[RecordError]:
    if isinstance(item, RecordError):
        return item
    try:
        if isinstance(item, ResourceWithRelations):
            resource_create_instance = item.resource
            _create_or_fetch_related_objects(session, item)
        else:
            resource_create_instance = item
        existing = _get_existing_resource(
            session, resource_create_instance, connector.resource_class
        )
        # TODO: if not None, update (https://github.com/aiondemand/AIOD-rest-api/issues/131)
        if existing is None:
            resource = router.create_resource(session, resource_create_instance, user)
            publish_resource(session, resource)

    except Exception as e:
        session.rollback()
        id_ = None
        if isinstance(item, AIoDConcept):
            id_ = item.platform_resource_identifier
        elif isinstance(item, ResourceWithRelations):
            id_ = item.resource.platform_resource_identifier
        elif isinstance(item, RecordError):
            id_ = item.identifier
        return RecordError(identifier=id_, error=e)  # type:ignore
    session.flush()
    return None


def _create_or_fetch_related_objects(session: Session, item: ResourceWithRelations):
    """
    For all resources in the `related_resources`, get the identifier, by either
    inserting them in the database, or retrieving the existing values, and put the identifiers
    into the item.resource.[field_name]
    """
    for field_name, related_resource_or_list in item.related_resources.items():
        if isinstance(related_resource_or_list, AIoDConcept):
            resources = [related_resource_or_list]
        else:
            resources = related_resource_or_list
        identifiers = []
        for resource in resources:
            if (
                resource.platform is not None
                and resource.platform != PlatformName.aiod
                and resource.platform_resource_identifier is not None
            ):
                # Get the router of this resource. The difficulty is, that the resource will be a
                # ResourceRead (e.g. a DatasetRead). So we search for the router for which the
                # resource name starts with the research-read-name

                resource_read_str = type(resource).__name__  # E.g. DatasetRead
                (router,) = [
                    router
                    for router in resource_routers.router_list
                    if resource_read_str.startswith(router.resource_class.__name__)
                    # E.g. "DatasetRead".startswith("Dataset")
                ]
                existing = _get_existing_resource(session, resource, router.resource_class)
                if existing is None:
                    created_resource = router.create_resource(session, resource)
                    publish_resource(session, created_resource)
                    identifiers.append(created_resource.identifier)
                else:
                    identifiers.append(existing.identifier)

        if isinstance(related_resource_or_list, AIoDConcept):
            (id_,) = identifiers
            item.resource.__setattr__(field_name, id_)  # E.g. Dataset.license_identifier = 1
        else:
            item.resource.__setattr__(field_name, identifiers)  # E.g. Dataset.keywords = [1, 4]


def publish_resource(session: Session, item: AIoDConcept):
    if hasattr(item, "aiod_entry"):
        item.aiod_entry.status = EntryStatus.PUBLISHED
    session.add(item)
    session.commit()
    return item


def main():
    args = _parse_args()

    setup_logger()
    sys.excepthook = exception_handler

    module_path = ".".join(args.connector.split(".")[0:-1])
    connector_cls_name = args.connector.split(".")[-1]
    module = importlib.import_module(module_path)
    connector: ResourceConnector = getattr(module, connector_cls_name)()

    working_dir = pathlib.Path(args.working_dir)
    error_path = working_dir / RELATIVE_PATH_ERROR_CSV
    state_path = working_dir / RELATIVE_PATH_STATE_JSON
    if args.remove_state and working_dir.exists():
        state_path.unlink(missing_ok=True)
        error_path.unlink(missing_ok=True)

    working_dir.mkdir(parents=True, exist_ok=True)

    first_run = not state_path.exists()

    with DbSession() as session:
        db_empty = session.scalars(select(connector.resource_class)).first() is None

    if first_run or db_empty:
        state = {}
        state_path.unlink(missing_ok=True)
        error_path.unlink(missing_ok=True)
    else:
        with open(state_path, "r") as f:
            state = json.load(f)
    items = connector.run(
        state=state,
        from_identifier=args.from_identifier,
        from_incl=args.from_date,
        limit=args.limit,
    )

    (router,) = [
        router
        for router in resource_routers.versioned_routers.get(Version.LATEST)
        + enum_routers.router_list
        if router.resource_class == connector.resource_class
    ]

    class ConnectorUser:
        def is_connector(self) -> bool:
            return True

        def is_connector_for_platform(self, platform: str) -> bool:
            return platform == connector.platform_name

    with DbSession() as session:
        for i, item in enumerate(items):
            error = save_to_database(
                router=router, connector=connector, session=session, item=item, user=ConnectorUser()
            )
            if error:
                if not error.ignore:
                    if isinstance(error.error, str):
                        logging.error(f"Error on identifier {error.identifier}: {error.error}")
                    else:
                        logging.error(
                            f"Error on identifier {error.identifier}", exc_info=error.error
                        )
                    with open(error_path, "a") as f:
                        error_cleaned = "".join(
                            c if c.isalnum() or c == "" else "_" for c in str(error.error)
                        )
                        f.write(f'"{error.identifier}","{error_cleaned}"\n')  # noqa: E231
            if args.save_every and i > 0 and i % args.save_every == 0:
                logging.info(f"Saving state after handling {i}th result: {json.dumps(state)}")
                with open(state_path, "w") as f:
                    json.dump(state, f, indent=4)
    with open(state_path, "w") as f:
        json.dump(state, f, indent=4)
    logging.info("Done")


if __name__ == "__main__":
    main()
