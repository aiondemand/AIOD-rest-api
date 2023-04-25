import copy

import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import Session
from starlette.testclient import TestClient
from datetime import datetime

from database.model.general import OrmKeyword
from database.model.news import OrmNews, OrmNewsCategory, OrmBusinessCategory
from platform_names import PlatformName


def test_happy_path_for_all(client: TestClient, engine: Engine):
    date_format = "%Y-%m-%d"
    news = [
        OrmNews(
            platform=PlatformName.aiod,
            platform_identifier=None,
            title="n1",
            body="b1",
            section="s1",
            headline="h1",
            source="s1",
            date_modified=datetime.strptime("2023-03-21", date_format),
            alternative_headline="ah1",
            word_count=10,
            news_categories=[OrmNewsCategory(category="something")],
            business_categories=[OrmBusinessCategory(category="something")],
            keywords=[OrmKeyword(name="something")],
        ),
        OrmNews(
            platform=PlatformName.aiod,
            platform_identifier=None,
            title="n2",
            body="b2",
            section="s2",
            headline="h2",
            source="s2",
            date_modified=datetime.strptime("2023-03-21", date_format),
            alternative_headline="ah2",
            word_count=10,
        ),
        OrmNews(
            platform=PlatformName.aiod,
            platform_identifier=None,
            title="n3",
            body="b3",
            section="s3",
            headline="h3",
            source="s3",
            date_modified=datetime.strptime("2023-03-21", date_format),
            alternative_headline="ah3",
            word_count=10,
        ),
    ]
    with Session(engine) as session:
        # Populate database
        session.add_all(news)
        session.commit()

    response = client.get("/news/v0")
    assert response.status_code == 200
    response_json = response.json()
    assert len(response_json) == 3
    assert {ds["title"] for ds in response_json} == {"n1", "n2", "n3"}
    assert {ds["body"] for ds in response_json} == {"b1", "b2", "b3"}
    assert {ds["section"] for ds in response_json} == {"s1", "s2", "s3"}
    assert {ds["headline"] for ds in response_json} == {"h1", "h2", "h3"}
    assert {ds["source"] for ds in response_json} == {"s1", "s2", "s3"}
    assert {ds["date_modified"] for ds in response_json} == {"2023-03-21T00:00:00"}
    assert {ds["alternative_headline"] for ds in response_json} == {"ah1", "ah2", "ah3"}
    assert {ds["word_count"] for ds in response_json} == {10, 10, 10}
    assert {len(ds["news_categories"]) for ds in response_json} == {0, 1}
    assert {len(ds["business_categories"]) for ds in response_json} == {0, 1}
    assert {len(ds["keywords"]) for ds in response_json} == {0, 1}
    for ds in response_json:
        assert len(ds) == 15


@pytest.mark.parametrize("news_id", [1, 2])
def test_happy_path_for_one(client: TestClient, engine: Engine, news_id: int):
    date_format = "%Y-%m-%d"
    news = [
        OrmNews(
            platform=PlatformName.aiod,
            platform_identifier=None,
            title="n1",
            body="b1",
            section="s1",
            headline="h1",
            source="s1",
            date_modified=datetime.strptime("2023-03-21", date_format),
            alternative_headline="ah1",
            word_count=10,
            news_categories=[OrmNewsCategory(category="something")],
            business_categories=[OrmBusinessCategory(category="something")],
            keywords=[OrmKeyword(name="something")],
        ),
        OrmNews(
            platform=PlatformName.aiod,
            platform_identifier=None,
            title="n2",
            body="b2",
            section="s2",
            headline="h2",
            source="s2",
            date_modified=datetime.strptime("2023-03-21", date_format),
            alternative_headline="ah2",
            word_count=10,
        ),
        OrmNews(
            platform=PlatformName.aiod,
            platform_identifier=None,
            title="n3",
            body="b3",
            section="s3",
            headline="h3",
            source="s3",
            date_modified=datetime.strptime("2023-03-21", date_format),
            alternative_headline="ah3",
            word_count=10,
        ),
    ]

    expected = copy.deepcopy(news[news_id - 1])
    with Session(engine) as session:
        session.add_all(news)
        session.commit()

    response = client.get(f"/news/v0/{news_id}")
    assert response.status_code == 200
    response_json = response.json()

    assert response_json["body"] == expected.body
    assert response_json["section"] == expected.section
    assert response_json["identifier"] == news_id
    assert response_json["platform"] == "aiod"
    assert response_json["platform_identifier"] == str(news_id)
    assert len(response_json["news_categories"]) == (1 if news_id == 1 else 0)
    assert len(response_json["business_categories"]) == (1 if news_id == 1 else 0)

    assert len(response_json["keywords"]) == (1 if news_id == 1 else 0)
    assert len(response_json) == 15


@pytest.mark.parametrize("news_id", [-1, 2, 3])
def test_empty_db(client: TestClient, engine: Engine, news_id):
    response = client.get(f"/news/v0/{news_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == f"News '{news_id}' not found in the database."


@pytest.mark.parametrize("news_id", [-1, 2, 3])
def test_news_not_found(client: TestClient, engine: Engine, news_id):
    date_format = "%Y-%m-%d"
    news = [
        OrmNews(
            platform=PlatformName.aiod,
            platform_identifier=None,
            title="n1",
            body="b1",
            section="s1",
            headline="h1",
            source="s1",
            date_modified=datetime.strptime("2023-03-21", date_format),
            alternative_headline="ah1",
            word_count=10,
        ),
    ]
    with Session(engine) as session:
        # Populate database
        session.add_all(news)
        session.commit()
    response = client.get(f"/news/v0/{news_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == f"News '{news_id}' not found in the database."
