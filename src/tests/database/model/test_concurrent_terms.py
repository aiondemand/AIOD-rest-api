from sqlalchemy.engine import Engine
from sqlmodel import select

from database.model.ai_resource.keyword import Keyword
from database.model.serializers import create_terms
from database.session import DbSession


def test_term_created_by_another_request_is_reused(engine: Engine):
    """
    A term that is created by a concurrent request should be used instead of being inserted a
    second time. See https://github.com/aiondemand/AIOD-rest-api/issues/442
    """
    with DbSession() as other_request:
        keyword = Keyword(name="keyword1")
        other_request.add(keyword)
        other_request.commit()
        identifier = keyword.identifier

    with DbSession() as session:
        # The other request committed after this request read the keywords, so this request still
        # thinks it has to create 'keyword1' itself.
        terms = create_terms(session, Keyword, {"keyword1", "keyword2"})
        session.commit()
        assert sorted(term.name for term in terms) == ["keyword1", "keyword2"]
        assert [term.identifier for term in terms if term.name == "keyword1"] == [identifier]

    with DbSession() as session:
        keywords = session.scalars(select(Keyword)).all()
        assert sorted(keyword.name for keyword in keywords) == ["keyword1", "keyword2"]
