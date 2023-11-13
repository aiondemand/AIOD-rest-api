from typing import Optional

from sqlalchemy import Column, Integer, ForeignKey
from sqlmodel import SQLModel, Field, Relationship

from database.model.field_length import NORMAL, SHORT
from database.model.relationships import OneToOne
from database.model.serializers import CastDeserializer


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
    country: str | None = Field(
        default=None,
        description="The country as ISO 3166-1 alpha-3",
        schema_extra={"example": "BEL"},
        min_length=3,
        max_length=3,
    )


class AddressORM(AddressBase, table=True):  # type: ignore [call-arg]
    __tablename__ = "address"

    identifier: int | None = Field(primary_key=True)

    # TODO(jos): make country an enum. This is difficult though, because deserialization isn't
    #  working on non-main entities
    location_identifier: int | None = Field(
        sa_column=Column(Integer, ForeignKey("location.identifier", ondelete="CASCADE"))
    )
    location: Optional["LocationORM"] = Relationship(back_populates="address")


class Address(AddressBase):
    """A postal address"""


class LocationBase(SQLModel):
    pass


class LocationORM(LocationBase, table=True):  # type: ignore [call-arg]
    __tablename__ = "location"

    identifier: int | None = Field(primary_key=True)
    address: Optional["AddressORM"] = Relationship(
        back_populates="location", sa_relationship_kwargs={"uselist": False}
    )
    geo: Optional["GeoORM"] = Relationship(
        back_populates="location", sa_relationship_kwargs={"uselist": False}
    )
    contact_identifier: int | None = Field(
        sa_column=Column(Integer, ForeignKey("contact.identifier", ondelete="CASCADE"))
    )
    event_identifier: int | None = Field(
        sa_column=Column(Integer, ForeignKey("event.identifier", ondelete="CASCADE"))
    )

    class RelationshipConfig:
        address: Optional[Address] = OneToOne(deserializer=CastDeserializer(AddressORM))
        geo: Optional[Geo] = OneToOne(deserializer=CastDeserializer(GeoORM))


class Location(LocationBase):
    """A physical location"""

    address: Optional["Address"] = Field(default=None)
    geo: Optional["Geo"] = Field(default=None)
