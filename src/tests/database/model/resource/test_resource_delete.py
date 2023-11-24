from sqlmodel import select
from starlette.testclient import TestClient

from database.model.ai_resource.alternate_name import AlternateName
from database.model.ai_resource.keyword import Keyword
from database.model.ai_resource.relevantlink import RelevantLink
from database.model.ai_resource.resource_table import AIResourceORM
from database.model.annotations import datatype_of_field
from database.model.dataset.dataset import Dataset
from database.model.knowledge_asset.publication import Publication
from database.session import DbSession


def test_happy_path(client: TestClient):
    dataset_media = datatype_of_field(Dataset, "media")
    dataset_note = datatype_of_field(Dataset, "note")

    alternate_name_a = AlternateName(name="a")
    alternate_name_b = AlternateName(name="b")
    alternate_name_c = AlternateName(name="c")
    alternate_name_d = AlternateName(name="d")
    keyword_a = Keyword(name="a")
    keyword_b = Keyword(name="b")
    keyword_c = Keyword(name="c")
    keyword_d = Keyword(name="d")
    relevant_link_a = RelevantLink(name="a")
    relevant_link_b = RelevantLink(name="b")
    relevant_link_c = RelevantLink(name="c")
    relevant_link_d = RelevantLink(name="d")

    dataset_1 = Dataset(
        name="dataset 1",
        alternate_name=[alternate_name_a, alternate_name_b, alternate_name_c],
        keyword=[keyword_a, keyword_b, keyword_c],
        relevant_link=[relevant_link_a, relevant_link_b, relevant_link_c],
        media=[
            dataset_media(content_url="example.com/dataset1-a"),
            dataset_media(content_url="example.com/dataset1-b"),
        ],
        note=[dataset_note(value="dataset1-a"), dataset_note(value="dataset1-b")],
        ai_resource_identifier=AIResourceORM(type="dataset"),
    )
    dataset_2 = Dataset(
        name="dataset 2",
        alternate_name=[alternate_name_a, alternate_name_d],
        keyword=[keyword_a, keyword_d],
        relevant_link=[relevant_link_a, relevant_link_d],
        media=[
            dataset_media(content_url="example.com/dataset2-a"),
            dataset_media(content_url="example.com/dataset2-b"),
        ],
        note=[dataset_note(value="dataset2-a"), dataset_note(value="dataset2-b")],
        ai_resource_identifier=AIResourceORM(type="dataset"),
    )
    publication = Publication(
        name="publication",
        alternate_name=[alternate_name_b],
        keyword=[keyword_b],
        relevant_link=[relevant_link_b],
        ai_resource_identifier=AIResourceORM(type="publication"),
    )

    with DbSession() as session:
        session.add_all([dataset_1, dataset_2, publication])
        session.commit()
        session.delete(dataset_1)
        session.commit()
        assert len(session.scalars(select(Dataset)).all()) == 1
        assert len(session.scalars(select(Publication)).all()) == 1
        assert len(session.scalars(select(AIResourceORM)).all()) == 2
        dataset_medias = session.scalars(select(dataset_media)).all()
        alternate_names = session.scalars(select(AlternateName)).all()
        keywords = session.scalars(select(Keyword)).all()
        notes = session.scalars(select(dataset_note)).all()
        relevant_links = session.scalars(select(RelevantLink)).all()
        assert {distribution.content_url for distribution in dataset_medias} == {
            "example.com/dataset2-a",
            "example.com/dataset2-b",
        }
        assert {name.name for name in alternate_names} == {"a", "b", "d"}
        assert {keyword.name for keyword in keywords} == {"a", "b", "d"}
        assert {link.name for link in relevant_links} == {"a", "b", "d"}
        assert {note.value for note in notes} == {"dataset2-a", "dataset2-b"}
