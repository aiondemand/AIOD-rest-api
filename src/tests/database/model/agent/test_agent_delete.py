from sqlmodel import select
from starlette.testclient import TestClient

from database.model.agent.agent_table import AgentTable
from database.model.agent.organisation import Organisation
from database.model.agent.person import Person
from database.session import DbSession


def test_happy_path(client: TestClient):
    organisation = Organisation(
        name="organisation",
        agent_identifier=AgentTable(type="organisation"),
    )
    person = Person(
        name="person",
        agent_identifier=AgentTable(type="person"),
    )

    with DbSession() as session:
        session.add(person)
        session.merge(organisation)
        session.commit()
        session.delete(person)
        session.commit()
        assert len(session.scalars(select(Person)).all()) == 0
        assert len(session.scalars(select(Organisation)).all()) == 1
        assert len(session.scalars(select(AgentTable)).all()) == 1
