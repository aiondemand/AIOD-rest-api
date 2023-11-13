from typing import Optional, TYPE_CHECKING

from sqlalchemy import Column, Integer, ForeignKey
from sqlmodel import Field, Relationship

from database.model.agent.email import Email
from database.model.agent.location import LocationORM, Location
from database.model.agent.telephone import Telephone
from database.model.concept.concept import AIoDConceptBase, AIoDConcept
from database.model.field_length import NORMAL
from database.model.helper_functions import many_to_many_link_factory
from database.model.relationships import ManyToMany, OneToMany, OneToOne
from database.model.serializers import (
    AttributeSerializer,
    CastDeserializer,
    FindByNameDeserializer,
)

if TYPE_CHECKING:
    from database.model.agent.person import Person
    from database.model.agent.organisation import Organisation


class ContactBase(AIoDConceptBase):
    name: str | None = Field(
        max_length=NORMAL,
        schema_extra={
            "example": "The name of this contact, especially useful if "
            "it is not known whether this contact is a person "
            "or organisation. For persons, it is preferred to "
            "store this information as contact.person.surname "
            "and contact.person.firstname. For organisations, "
            "store it as contact.organisation.legal_name."
        },
    )


class Contact(ContactBase, AIoDConcept, table=True):  # type: ignore [call-arg]
    __tablename__ = "contact"
    identifier: int = Field(default=None, primary_key=True)

    email: list[Email] = Relationship(
        link_model=many_to_many_link_factory(table_from="contact", table_to=Email.__tablename__)
    )
    location: list[LocationORM] = Relationship(sa_relationship_kwargs={"cascade": "all, delete"})
    telephone: list[Telephone] = Relationship(
        link_model=many_to_many_link_factory(table_from="contact", table_to=Telephone.__tablename__)
    )
    organisation_identifier: int | None = Field(
        sa_column=Column(Integer, ForeignKey("organisation.identifier"))
    )
    organisation: Optional["Organisation"] = Relationship(
        back_populates="contact_details", sa_relationship_kwargs={"uselist": False}
    )
    person_identifier: int | None = Field(
        sa_column=Column(Integer, ForeignKey("person.identifier"))
    )
    person: Optional["Person"] = Relationship(
        back_populates="contact_details", sa_relationship_kwargs={"uselist": False}
    )

    class RelationshipConfig(AIoDConcept.RelationshipConfig):
        email: list[str] = ManyToMany(
            description="An email address.",
            _serializer=AttributeSerializer("name"),
            deserializer=FindByNameDeserializer(Email),
            on_delete_trigger_orphan_deletion=lambda: ["contact_email_link"],
            default_factory_pydantic=list,
        )
        location: list[Location] = OneToMany(
            deserializer=CastDeserializer(LocationORM),
            default_factory_pydantic=list,  # no deletion trigger: cascading delete is used
        )
        telephone: list[str] = ManyToMany(
            description="A telephone number, including the land code.",
            _serializer=AttributeSerializer("name"),
            deserializer=FindByNameDeserializer(Telephone),
            on_delete_trigger_orphan_deletion=lambda: ["contact_telephone_link"],
            default_factory_pydantic=list,
        )
        organisation: Optional[int] = OneToOne(
            _serializer=AttributeSerializer("identifier"),
        )
        person: Optional[int] = OneToOne(
            _serializer=AttributeSerializer("identifier"),
        )

    @property
    def contact_name(self) -> str | None:
        if self.organisation and self.organisation.legal_name:
            return self.organisation.legal_name
        if self.person and (self.person.surname or self.person.given_name):
            return ", ".join(
                [name for name in (self.person.surname, self.person.given_name) if name]
            )
        return self.name
