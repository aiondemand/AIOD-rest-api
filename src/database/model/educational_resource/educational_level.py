from database.model.named_relation import NamedRelation


class EducationalLevel(NamedRelation, table=True):  # type: ignore [call-arg]
    __tablename__ = "edu_educational_level"
