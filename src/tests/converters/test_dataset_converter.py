import copy

import pytest
from fastapi import HTTPException
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from converters import dataset_converter_instance
from database.model.dataset import OrmDataset, OrmAlternateName, OrmDataDownload, OrmMeasuredValue
from database.model.general import OrmLicense, OrmKeyword
from database.model.publication import OrmPublication
from schemas import AIoDDataset

DATASET_RELATION_FIELDS = (
    "license",
    "has_parts",
    "is_part",
    "alternate_names",
    "citations",
    "distributions",
    "keywords",
    "measured_values",
)


def test_aiod_to_orm_happy_path(
    engine: Engine,
    orm_dataset: OrmDataset,
    aiod_dataset: AIoDDataset,
    orm_publication: OrmPublication,
):
    has_parts = {1, 2, 3}
    is_part = {4, 5, 6}
    citations = {7, 8, 9}

    related_datasets = []
    for related_dataset_id in has_parts | is_part:
        ds = copy.deepcopy(orm_dataset)
        ds.same_as = f"url_{related_dataset_id}"
        ds.name = f"name_{related_dataset_id}"
        ds.platform_identifier = str(related_dataset_id)
        related_datasets.append(ds)

    related_publications = []
    for related_publication_id in citations:
        p = copy.deepcopy(orm_publication)
        p.platform_identifier = str(related_publication_id)
        related_publications.append(p)

    with Session(engine) as session:
        session.add_all(related_datasets)
        session.add_all(related_publications)
        session.commit()

    aiod = copy.deepcopy(aiod_dataset)
    aiod.platform_identifier = "10"
    aiod.has_parts = has_parts
    aiod.is_part = is_part
    aiod.citations = citations

    with Session(engine) as session:
        orm = dataset_converter_instance.aiod_to_orm(session, aiod)
        session.add(orm)
        session.commit()
        for field, expected_value in aiod.__dict__.items():
            if field not in DATASET_RELATION_FIELDS and field != "identifier":
                assert orm.__getattribute__(field) == expected_value, f"Error for field {field}"

        assert orm.license.name == aiod.license
        assert orm.license.datasets == [orm]

        assert {ds.identifier for ds in orm.has_parts} == has_parts
        assert all({p.identifier for p in ds.is_part} == {orm.identifier} for ds in orm.has_parts)
        assert {ds.identifier for ds in orm.is_part} == is_part
        assert all({p.identifier for p in ds.has_parts} == {orm.identifier} for ds in orm.is_part)

        assert {a.name for a in orm.alternate_names} == set(aiod.alternate_names)
        assert all(
            {ds.identifier for ds in a.datasets} == {orm.identifier} for a in orm.alternate_names
        )
        assert {c.identifier for c in orm.citations} == citations
        assert all({ds.identifier for ds in p.datasets} == {orm.identifier} for p in orm.citations)
        assert {k.name for k in orm.keywords} == {"a", "b", "c"}
        assert all({ds.identifier for ds in p.datasets} == {orm.identifier} for p in orm.citations)

        assert len(orm.distributions) == 1
        for field, expected_value in aiod.distributions[0].__dict__.items():
            assert orm.distributions[0].__getattribute__(field) == expected_value, (
                f"Error on " f"field {field}"
            )

        assert len(orm.measured_values) == 1
        assert orm.measured_values[0].variable == "variable"
        assert orm.measured_values[0].technique == "technique"


def test_aiod_to_orm_unexisting_dataset(
    engine: Engine, orm_dataset: OrmDataset, aiod_dataset: AIoDDataset
):
    related_datasets = []
    for related_dataset_id in {1, 2}:
        ds = copy.deepcopy(orm_dataset)
        ds.same_as = f"url_{related_dataset_id}"
        ds.name = f"name_{related_dataset_id}"
        ds.platform_identifier = str(related_dataset_id)
        related_datasets.append(ds)

    with Session(engine) as session:
        session.add_all(related_datasets)
        session.commit()

    aiod = copy.deepcopy(aiod_dataset)
    aiod.platform_identifier = "7"
    aiod.has_parts = {1, 2, 3, 4}

    with Session(engine) as session:
        with pytest.raises(HTTPException) as e:
            dataset_converter_instance.aiod_to_orm(session, aiod)
        assert (
            e.value.detail == "Related OrmDataset's with identifiers 3, 4 not found in the "
            "database."
        )


def test_orm_to_aiod(
    orm_dataset: OrmDataset, orm_publication: OrmPublication, orm_data_download: OrmDataDownload
):
    has_parts = {1, 2, 3}
    is_part = {4, 5, 6}
    citations = {1, 2, 3}

    orm = copy.deepcopy(orm_dataset)
    orm.license = OrmLicense(name="license.name")
    orm.alternate_names = [OrmAlternateName(name="alias1"), OrmAlternateName(name="alias2")]
    orm.distributions = [orm_data_download]
    orm.keywords = [OrmKeyword(name="a"), OrmKeyword(name="b")]
    orm.measured_values = [OrmMeasuredValue(variable="variable", technique="technique")]

    for related_dataset_id in has_parts | is_part:
        ds = copy.deepcopy(orm_dataset)
        ds.identifier = related_dataset_id
        ds.same_as = f"url_{related_dataset_id}"
        ds.name = f"name_{related_dataset_id}"
        ds.platform_identifier = str(related_dataset_id)
        if related_dataset_id in has_parts:
            orm.has_parts.append(ds)
        else:
            orm.is_part.append(ds)

    for related_publication_id in citations:
        p = copy.deepcopy(orm_publication)
        p.identifier = related_publication_id
        p.platform_identifier = str(related_publication_id)
        orm.citations.append(p)

    aiod = dataset_converter_instance.orm_to_aiod(orm)

    for field, actual_value in aiod.__dict__.items():
        if field not in DATASET_RELATION_FIELDS:
            expected_value = orm.__getattribute__(field)
            assert actual_value == expected_value, f"Error for field {field}"

    assert aiod.license == orm.license.name
    assert aiod.has_parts == has_parts
    assert aiod.is_part == is_part
    assert aiod.alternate_names == {"alias1", "alias2"}
    assert aiod.citations == citations
    assert aiod.keywords == {"a", "b"}
    assert len(aiod.distributions) == 1
    for field, actual_value in aiod.distributions[0].__dict__.items():
        expected_value = orm_data_download.__getattribute__(field)
        assert actual_value == expected_value, f"Error on " f"field {field}"
    assert len(aiod.measured_values) == 1
    assert aiod.measured_values[0].variable == "variable"
    assert aiod.measured_values[0].technique == "technique"
