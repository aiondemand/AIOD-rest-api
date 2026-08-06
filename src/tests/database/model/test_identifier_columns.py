from sqlalchemy.dialects import mysql
from sqlmodel import SQLModel

import main  # noqa: F401  # importing main makes sure all tables are registered on the metadata
from database.identifiers import IDENTIFIER_TYPE


def test_identifier_columns_are_case_sensitive():
    """
    Every column that refers to an identifier should be created with the same case sensitive
    collation as the identifier it refers to. See
    https://github.com/aiondemand/AIOD-rest-api/issues/648
    """
    dialect = mysql.dialect()
    identifier_ddl = IDENTIFIER_TYPE.compile(dialect)
    assert identifier_ddl == "VARCHAR(30) COLLATE utf8mb3_bin"

    mismatched = [
        f"{table.name}.{column.name}"
        for table in SQLModel.metadata.tables.values()
        # The test suite registers tables of its own on the same metadata, we skip those.
        if not table.name.startswith("test_")
        for column in table.columns
        for foreign_key in column.foreign_keys
        if foreign_key.column.type.compile(dialect) == identifier_ddl
        and column.type.compile(dialect) != identifier_ddl
    ]
    assert not mismatched
