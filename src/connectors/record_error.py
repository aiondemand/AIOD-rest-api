import dataclasses


@dataclasses.dataclass
class RecordError:
    identifier: str | None
    error: BaseException | str
    ignore: bool = False
