from database.model.named_relation import Taxonomy


class IndustrialSector(Taxonomy, table=True):  # type: ignore [call-arg]
    __tablename__ = "industrial_sector"
