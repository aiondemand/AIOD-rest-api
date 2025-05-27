import datetime

from sqlmodel import select

from database.deletion import hard_delete
from database.model.concept.aiod_entry import AIoDEntryORM, EntryStatus
from database.session import DbSession
from tests.testutils.test_resource import factory_test_resource, TestResource


def test_hard_delete():
    now = datetime.datetime.now()
    deletion_time = now - datetime.timedelta(seconds=10)
    with DbSession() as session:
        session.add_all(
            [
                factory_test_resource(title="test_resource_to_keep", status=EntryStatus.DRAFT,
                                      platform="example", platform_resource_identifier=1,
                                      date_deleted=None),
                factory_test_resource(title="test_resource_to_keep_2", status=EntryStatus.DRAFT,
                                      platform="example", platform_resource_identifier=2,
                                      date_deleted=now),
                factory_test_resource(title="my_test_resource", status=EntryStatus.DRAFT,
                                      platform="example", platform_resource_identifier=3,
                                      date_deleted=deletion_time),
                factory_test_resource(title="second_test_resource", status=EntryStatus.DRAFT,
                                      platform="example", platform_resource_identifier=4,
                                      date_deleted=deletion_time),
            ]
        )
        session.commit()

    hard_delete.hard_delete_older_than(datetime.timedelta(seconds=5))
    with DbSession() as session:
        resources = session.scalars(select(TestResource)).all()
        assert len(resources) == 2
        assert {r.platform_resource_identifier for r in resources} == {"1", "2"}

        entries = session.scalars(select(AIoDEntryORM)).all()
        assert len(entries) == 2
