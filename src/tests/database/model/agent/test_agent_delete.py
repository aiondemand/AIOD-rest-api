from sqlalchemy.engine import Engine
from sqlmodel import Session, select
from starlette.testclient import TestClient

from database.model.agent.agent_table import AgentTable
from database.model.agent.email import Email
from database.model.agent.organisation import Organisation
from database.model.agent.person import Person
from database.model.agent.telephone import Telephone


def test_happy_path(
    client: TestClient,
    engine: Engine,
):
    email_a = Email(name="a@example.com")
    email_b = Email(name="b@example.com")
    email_c = Email(name="c@example.com")
    phone_a = Telephone(name="123")
    phone_b = Telephone(name="456")
    phone_c = Telephone(name="789")
    organisation = Organisation(
        name="organisation",
        email=[email_a, email_b],
        telephone=[phone_a, phone_b],
        agent_identifier=AgentTable(type="organisation"),
    )
    person = Person(
        name="person",
        email=[email_a, email_c],
        telephone=[phone_a, phone_c],
        agent_identifier=AgentTable(type="person"),
    )

    with Session(engine) as session:
        session.add(person)
        session.merge(organisation)
        session.commit()
        session.delete(person)
        session.commit()
        assert len(session.scalars(select(Person)).all()) == 0
        assert len(session.scalars(select(Organisation)).all()) == 1
        assert len(session.scalars(select(AgentTable)).all()) == 1
        emails = session.scalars(select(Email)).all()
        phones = session.scalars(select(Telephone)).all()
        assert {email.name for email in emails} == {email_a.name, email_b.name}
        assert {phone.name for phone in phones} == {phone_a.name, phone_b.name}
