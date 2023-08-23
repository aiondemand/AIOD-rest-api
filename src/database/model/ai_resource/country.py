# from sqlmodel import Relationship
#
# from database.model.named_relation import NamedRelation
# from typing import TYPE_CHECKING
#
# if TYPE_CHECKING:
#     from database.model.new.ai_resource.location import AddressORM
#
#
# class Country(NamedRelation, table=True):  # type: ignore [call-arg]
#     __tablename__ = "country"
#
#     addresses: list["AddressORM"] = Relationship(back_populates="country")
