from database.model.named_relation import NamedRelation


class IndustrialSector(NamedRelation, table=True):  # type: ignore [call-arg]
    __tablename__ = "industrial_sector"
