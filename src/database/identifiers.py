import random
import string
from typing import Callable

from sqlalchemy import String
from sqlalchemy.dialects import mysql

from database.model.field_length import IDENTIFIER_LENGTH

# The type of every column that holds an identifier. Identifiers must be matched case-sensitively:
# SQLite is case-sensitive by default, MySQL is not, so there we ask for a binary collation
# explicitly. The same collation is set on existing databases by the identifier migrations.
IDENTIFIER_TYPE = String(length=IDENTIFIER_LENGTH).with_variant(
    mysql.VARCHAR(length=IDENTIFIER_LENGTH, collation="utf8mb3_bin"), "mysql"
)


def create_id_generator(
    prefix: str = "temp", seperator: str = "_", n: int = 24
) -> Callable[[], str]:
    if len(prefix) > 4:
        raise ValueError(f"Provided prefix {prefix!r} must contain at most 4 characters.")
    if len(seperator) > 1:
        raise ValueError(f"Provided seperator {seperator!r} must contain at most 1 characters.")

    alpha_numeric = string.ascii_letters + string.digits

    def generate_identifier() -> str:
        random_string = "".join(random.choices(alpha_numeric, k=n))  # noqa: S311  # non-crypto application
        return f"{prefix}{seperator}{random_string}"

    return generate_identifier
