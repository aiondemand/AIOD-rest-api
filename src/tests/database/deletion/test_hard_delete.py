import datetime
from unittest.mock import Mock

from sqlalchemy.future import Engine
from sqlmodel import Session, select

from authentication import keycloak_openid
from database.deletion import hard_delete
from database.model.concept.aiod_entry import AIoDEntryORM
from database.model.concept.status import Status
from tests.testutils.test_resource import test_resource_factory, TestResource


def test_hard_delete(
    engine_test_resource: Engine,
    mocked_privileged_token: Mock,
    draft: Status,
):
    keycloak_openid.userinfo = mocked_privileged_token

    now = datetime.datetime.now()
    deletion_time = now - datetime.timedelta(seconds=10)
    with Session(engine_test_resource) as session:
        session.add_all(
            [
                test_resource_factory(
                    title="test_resource_to_keep",
                    platform="example",
                    platform_resource_identifier=1,
                    status=draft,
                    date_deleted=None,
                ),
                test_resource_factory(
                    title="test_resource_to_keep_2",
                    platform="example",
                    platform_resource_identifier=2,
                    status=draft,
                    date_deleted=now,
                ),
                test_resource_factory(
                    title="my_test_resource",
                    platform="example",
                    platform_resource_identifier=3,
                    status=draft,
                    date_deleted=deletion_time,
                ),
                test_resource_factory(
                    title="second_test_resource",
                    platform="example",
                    platform_resource_identifier=4,
                    status=draft,
                    date_deleted=deletion_time,
                ),
            ]
        )
        session.commit()

    hard_delete.hard_delete_older_than(engine_test_resource, datetime.timedelta(seconds=5))
    with Session(engine_test_resource) as session:
        resources = session.scalars(select(TestResource)).all()
        assert len(resources) == 2
        assert {r.platform_resource_identifier for r in resources} == {"1", "2"}

        entries = session.scalars(select(AIoDEntryORM)).all()
        assert len(entries) == 2
