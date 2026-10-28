from sqlalchemy.dialects import mysql
from sqlmodel import SQLModel

import main  # noqa: F401  # importing main makes sure all tables are registered on the metadata
from routers.resource_routers.organisation_router import MAX_FILE_SIZE_BYTES

MEDIUMBLOB_MAX_BYTES = 2**24 - 1


def test_binary_blob_columns_hold_the_largest_image():
    """
    On MySQL, every binary_blob column should hold the largest image the image endpoints accept.
    A BLOB holds at most 65,535 bytes, so MySQL inserts of larger images fail.
    """
    assert MAX_FILE_SIZE_BYTES <= MEDIUMBLOB_MAX_BYTES  # noqa: S101

    dialect = mysql.dialect()
    column_types = {
        f"{table.name}.{column.name}": column.type.compile(dialect)
        for table in SQLModel.metadata.tables.values()
        # The test suite registers tables of its own on the same metadata, we skip those.
        if not table.name.startswith("test_")
        for column in table.columns
        if column.name == "binary_blob"
    }
    mismatched = [name for name, type_ in column_types.items() if type_ != "MEDIUMBLOB"]
    assert column_types  # noqa: S101
    assert not mismatched  # noqa: S101
