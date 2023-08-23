from database.model.named_relation import NamedRelation


class OrganisationType(NamedRelation, table=True):  # type: ignore [call-arg]
    __tablename__ = "organisation_type"
