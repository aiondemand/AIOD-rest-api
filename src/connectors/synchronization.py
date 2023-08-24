import argparse
import importlib
import json
import logging
import pathlib
import shutil
import sys
from datetime import datetime
from typing import Optional

from sqlmodel import Session

import routers
from connectors.abstract.resource_connector import ResourceConnector, RESOURCE
from connectors.record_error import RecordError
from connectors.resource_with_relations import ResourceWithRelations
from database.model.concept.concept import AIoDConcept
from database.setup import _create_or_fetch_related_objects, _get_existing_resource, sqlmodel_engine
from routers import ResourceRouter

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
        type=lambda d: datetime.strptime(d, "%Y-%m-%d").date(),
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
            router.create_resource(session, resource_create_instance)

    except Exception as e:
        session.rollback()
        id_ = None
        if isinstance(item, AIoDConcept):
            id_ = item.platform_identifier
        elif isinstance(item, ResourceWithRelations):
            id_ = item.resource.platform_identifier
        elif isinstance(item, RecordError):
            id_ = item.identifier
        return RecordError(identifier=id_, error=e)  # type:ignore
    session.flush()
    return None


def main():
    args = _parse_args()

    working_dir = pathlib.Path(args.working_dir)
    if args.remove_state and working_dir.exists():
        shutil.rmtree(working_dir)
    working_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    sys.excepthook = exception_handler

    module_path = ".".join(args.connector.split(".")[0:-1])
    connector_cls_name = args.connector.split(".")[-1]
    module = importlib.import_module(module_path)
    connector: ResourceConnector = getattr(module, connector_cls_name)()

    error_path = working_dir / RELATIVE_PATH_ERROR_CSV
    state_path = working_dir / RELATIVE_PATH_STATE_JSON
    error_path.parents[0].mkdir(parents=True, exist_ok=True)
    state_path.parents[0].mkdir(parents=True, exist_ok=True)
    first_run = not state_path.exists()

    if first_run:
        state = {}
    else:
        with open(state_path, "r") as f:
            state = json.load(f)

    items = connector.run(
        state=state,
        from_identifier=args.from_identifier,
        from_date=args.from_date,
        limit=args.limit,
    )

    (router,) = [
        router
        for router in routers.resource_routers
        if router.resource_class == connector.resource_class
    ]

    engine = sqlmodel_engine(rebuild_db="never", create_if_not_exists=False)

    with Session(engine) as session:
        for i, item in enumerate(items):
            error = save_to_database(router=router, connector=connector, session=session, item=item)
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
                        f.write(f'"{error.identifier}","{error_cleaned}"\n')
            if args.save_every and i > 0 and i % args.save_every == 0:
                logging.info(f"Saving state after handling {i}th result: {json.dumps(state)}")
                with open(state_path, "w") as f:
                    json.dump(state, f, indent=4)
                session.commit()
    with open(state_path, "w") as f:
        session.commit()
        json.dump(state, f, indent=4)
    logging.info("Done")


if __name__ == "__main__":
    main()
