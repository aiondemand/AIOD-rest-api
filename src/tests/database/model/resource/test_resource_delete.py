from sqlalchemy.engine import Engine
from sqlmodel import Session, select
from starlette.testclient import TestClient

from database.model.ai_resource.alternate_name import AlternateName
from database.model.ai_resource.keyword import Keyword
from database.model.ai_resource.resource_table import AIResourceTable
from database.model.dataset.dataset import Dataset
from database.model.knowledge_asset.publication import Publication


def test_happy_path(
    client: TestClient,
    engine: Engine,
):
    dataset_media = Dataset.__annotations__["media"].__args__[0]
    dataset_note = Dataset.__annotations__["note"].__args__[0]

    alternate_name_a = AlternateName(name="name_a")
    alternate_name_b = AlternateName(name="name_b")
    alternate_name_c = AlternateName(name="name_c")
    alternate_name_d = AlternateName(name="name_d")
    keyword_a = Keyword(name="keyword_a")
    keyword_b = Keyword(name="keyword_b")
    keyword_c = Keyword(name="keyword_c")
    keyword_d = Keyword(name="keyword_d")
    dataset_1 = Dataset(
        name="dataset 1",
        alternate_name=[alternate_name_a, alternate_name_b, alternate_name_c],
        keyword=[keyword_a, keyword_b, keyword_c],
        media=[
            dataset_media(content_url="example.com/dataset1-a"),
            dataset_media(content_url="example.com/dataset1-b"),
        ],
        note=[dataset_note(value="dataset1-a"), dataset_note(value="dataset1-b")],
        ai_resource_identifier=AIResourceTable(type="dataset"),
    )
    dataset_2 = Dataset(
        name="dataset 2",
        alternate_name=[alternate_name_a, alternate_name_d],
        keyword=[keyword_a, keyword_d],
        media=[
            dataset_media(content_url="example.com/dataset2-a"),
            dataset_media(content_url="example.com/dataset2-b"),
        ],
        note=[dataset_note(value="dataset2-a"), dataset_note(value="dataset2-b")],
        ai_resource_identifier=AIResourceTable(type="dataset"),
    )
    publication = Publication(
        name="publication",
        alternate_name=[alternate_name_b],
        keyword=[keyword_b],
        ai_resource_identifier=AIResourceTable(type="publication"),
    )

    with Session(engine) as session:
        session.add_all([dataset_1, dataset_2, publication])
        session.commit()
        session.delete(dataset_1)
        session.commit()
        assert len(session.scalars(select(Dataset)).all()) == 1
        assert len(session.scalars(select(Publication)).all()) == 1
        assert len(session.scalars(select(AIResourceTable)).all()) == 2
        dataset_medias = session.scalars(select(dataset_media)).all()
        keywords = session.scalars(select(Keyword)).all()
        notes = session.scalars(select(dataset_note)).all()
        assert {distribution.content_url for distribution in dataset_medias} == {
            "example.com/dataset2-a",
            "example.com/dataset2-b",
        }
        assert {keyword.name for keyword in keywords} == {
            keyword_a.name,
            keyword_b.name,
            keyword_d.name,
        }
        assert {note.value for note in notes} == {"dataset2-a", "dataset2-b"}
