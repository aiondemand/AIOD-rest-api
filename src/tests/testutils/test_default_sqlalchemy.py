import os
import tempfile

import pytest

from database.session import EngineSingleton
from tests.testutils import default_sqlalchemy


def test_engine_fixture_uses_non_deleting_temp_file_and_cleans_up(monkeypatch):
    captured: dict[str, object] = {}
    original_named_temporary_file = tempfile.NamedTemporaryFile

    def tracked_named_temporary_file(*args, **kwargs):
        captured["kwargs"] = kwargs.copy()
        temporary_file = original_named_temporary_file(*args, **kwargs)
        captured["path"] = temporary_file.name
        return temporary_file

    monkeypatch.setattr(default_sqlalchemy.tempfile, "NamedTemporaryFile", tracked_named_temporary_file)

    original_engine = EngineSingleton().engine

    engine_generator = default_sqlalchemy.engine.__wrapped__()
    _ = next(engine_generator)

    temp_path = str(captured["path"])
    assert captured["kwargs"]["delete"] is False
    assert temp_path.endswith(".db")
    assert os.path.exists(temp_path)

    with pytest.raises(StopIteration):
        next(engine_generator)

    assert not os.path.exists(temp_path)

    EngineSingleton().patch(original_engine)
