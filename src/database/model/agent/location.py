from typing import Optional

from pydantic import validator
from sqlalchemy import Column, Integer, ForeignKey, String
from sqlmodel import SQLModel, Field, Relationship

from database.model.field_length import NORMAL, SHORT, IDENTIFIER_LENGTH
from database.model.relationships import OneToOne, ManyToOne
from database.model.serializers import CastDeserializer, AttributeSerializer, FindByNameDeserializer
from database.model.named_relation import create_taxonomy


class GeoBase(SQLModel):
    latitude: float | None = Field(
        default=None,
        description="The latitude of a location in degrees (WGS84)",
        schema_extra={"example": 37.42242},
    )
    longitude: float | None = Field(
        default=None,
        description="The longitude of a location in degrees (WGS84)",
        schema_extra={"example": -122.08585},
    )
    elevation_millimeters: int | None = Field(
        default=None,
        description="The elevation in millimeters with tespect to the WGS84 ellipsoid",
    )


class GeoORM(GeoBase, table=True):  # type: ignore [call-arg]
    __tablename__ = "geo"
    identifier: int | None = Field(primary_key=True)

    location_identifier: int | None = Field(
        sa_column=Column(Integer, ForeignKey("location.identifier", ondelete="CASCADE"))
    )
    location: Optional["LocationORM"] = Relationship(back_populates="geo")


class Geo(GeoBase):
    """The geographic coordinates of a physical location"""


Country = create_taxonomy(
    class_name="Country",
    table_name="country",
    plural_name="countries",
)


class AddressBase(SQLModel):
    region: str | None = Field(
        description="A subdivision of the country. Not necessary for most countries. ",
        max_length=NORMAL,
        default=None,
        schema_extra={"example": "California"},
    )
    locality: str | None = Field(
        description="A city, town or village.",
        max_length=NORMAL,
        default=None,
        schema_extra={"example": "Paris"},
    )
    street: str | None = Field(
        description="The street address.",
        default=None,
        max_length=NORMAL,
        schema_extra={"example": "Wetstraat 170"},
    )
    postal_code: str | None = Field(
        description="The postal code.",
        default=None,
        max_length=SHORT,
        schema_extra={"example": "1040 AA"},
    )
    address: str | None = Field(
        description="Free text, in case the separate parts such as the "
        "street, postal code and country cannot be confidently "
        "separated.",
        default=None,
        max_length=NORMAL,
        schema_extra={"example": "Wetstraat 170, 1040 Brussel"},
    )


class AddressORM(AddressBase, table=True):  # type: ignore [call-arg]
    __tablename__ = "address"

    identifier: int | None = Field(primary_key=True)

    location_identifier: int | None = Field(
        sa_column=Column(Integer, ForeignKey("location.identifier", ondelete="CASCADE"))
    )
    location: Optional["LocationORM"] = Relationship(back_populates="address")
    country_identifier: int | None = Field(
        foreign_key=f"{Country.__tablename__}.identifier",
    )
    country: Country | None = Relationship()  # type: ignore [valid-type]

    class RelationshipConfig:
        country: Optional[str] = ManyToOne(
            description="The country the address is from.",
            identifier_name="country_identifier",
            _serializer=AttributeSerializer("name"),
            deserializer=FindByNameDeserializer(Country),
            example="Germany",
        )


class Address(AddressBase):
    """A postal address"""

    country: str | None

    @validator("country", pre=True)
    def use_country_name(cls, v) -> str | None:
        if v is None or isinstance(v, str):
            return v
        if isinstance(v, Country):
            return v.name
        raise TypeError(f"Expected country to be `str` or `Country`, not {type(v)}.")


class LocationBase(SQLModel):
    pass


class LocationORM(LocationBase, table=True):  # type: ignore [call-arg]
    __tablename__ = "location"
    __plural__ = "locations"

    identifier: int | None = Field(primary_key=True)
    address: Optional["AddressORM"] = Relationship(
        back_populates="location", sa_relationship_kwargs={"uselist": False}
    )
    geo: Optional["GeoORM"] = Relationship(
        back_populates="location", sa_relationship_kwargs={"uselist": False}
    )
    contact_identifier: str | None = Field(
        sa_column=Column(
            String(IDENTIFIER_LENGTH), ForeignKey("contact.identifier", ondelete="CASCADE")
        )
    )
    event_identifier: str | None = Field(
        sa_column=Column(
            String(IDENTIFIER_LENGTH), ForeignKey("event.identifier", ondelete="CASCADE")
        )
    )

    class RelationshipConfig:
        address: Optional[Address] = OneToOne(deserializer=CastDeserializer(AddressORM))
        geo: Optional[Geo] = OneToOne(deserializer=CastDeserializer(GeoORM))


class Location(LocationBase):
    """A physical location"""

    address: Optional["Address"] = Field(default=None)
    geo: Optional["Geo"] = Field(default=None)
