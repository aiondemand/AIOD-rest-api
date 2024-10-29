import pytest

from database.validators import huggingface_validators


@pytest.mark.parametrize(
    "identifier,expected_error",
    [
        ("0-hero/OIG-small-chip2", None),
        ("user/Foo-BAR_foo.bar123", None),
        ("acronym_identification", None),
        (
            "user/data/set",
            ValueError(
                "Repo id must be in the form 'repo_name' or 'namespace/repo_name': "
                "'user/data/set'. Use `repo_type` argument if needed."
            ),
        ),
        (
            "",
            ValueError(
                "Repo id must use alphanumeric chars or '-', '_', '.', '--' and '..' are "
                "forbidden, '-' and '.' cannot start or end the name, max length is 96: "
                "''."
            ),
        ),
        (
            "user/" + "a" * 200,
            ValueError(
                "Repo id must use alphanumeric chars or '-', '_', '.', '--' and '..' are "
                "forbidden, '-' and '.' cannot start or end the name, max length is 96: "
                "'user/" + "a" * 200 + "'."
            ),
        ),
    ],
)
def test_identifier(identifier: str, expected_error: ValueError | None):
    if expected_error is None:
        huggingface_validators.throw_error_on_invalid_identifier(identifier)
    else:
        with pytest.raises(type(expected_error)) as exception_info:
            huggingface_validators.throw_error_on_invalid_identifier(identifier)
        assert exception_info.value.args[0] == expected_error.args[0]
