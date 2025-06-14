from pydantic import validator
from .loader import get_taxonomy_map

def taxonomy_field_validator(field_name: str):
    def _validator(cls, v):
        allowed = get_taxonomy_map().get(field_name, [])
        if v not in allowed:
            raise ValueError(f"'{v}' is not a valid {field_name!r}.")
        return v
    return validator(field_name, allow_reuse=True)(_validator)
