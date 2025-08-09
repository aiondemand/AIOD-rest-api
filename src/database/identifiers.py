import random
import string
from typing import Callable


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
