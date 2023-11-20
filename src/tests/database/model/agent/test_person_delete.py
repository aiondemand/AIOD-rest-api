from sqlalchemy.engine import Engine
from sqlmodel import Session, select
from starlette.testclient import TestClient

from database.model.agent.expertise import Expertise
from database.model.agent.person import Person


def test_happy_path(
    client: TestClient,
    engine: Engine,
):
    expertise_a = Expertise(name="just")
    expertise_b = Expertise(name="an")
    expertise_c = Expertise(name="example")
    person_a = Person(
        name="person a",
        expertise=[expertise_a, expertise_b],
    )
    person_b = Person(
        name="person b",
        expertise=[expertise_a, expertise_c],
    )

    with Session(engine) as session:
        session.add(person_a)
        session.add(person_b)
        session.commit()
        session.delete(person_a)
        session.commit()
        assert len(session.scalars(select(Person)).all()) == 1
        expertises = session.scalars(select(Expertise)).all()
        assert {expertise.name for expertise in expertises} == {expertise_a.name, expertise_c.name}
