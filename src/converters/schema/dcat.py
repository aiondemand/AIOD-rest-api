"""
Based on DCAT Application Profile for data portals in Europe Version 2.1.1

The DCAT Application Profile for data portals in Europe (DCAT-AP) is a specification based on W3C's
Data Catalogue vocabulary (DCAT) for describing public sector datasets in Europe. Its basic use
case is to enable a cross-data portal search for datasets and make public sector data better
searchable across borders and sectors. This can be achieved by the exchange of descriptions of data
sets among data portals
"""
import datetime
from abc import ABC
from typing import Union

from pydantic import BaseModel, Field, Extra


class DcatAPContext(BaseModel):
    dcat: str = Field(default="http://www.w3.org/ns/dcat", const=True)
    dct: str = Field(default="http://purl.org/dc/terms/", const=True)
    vcard: str = Field(default="https://www.w3.org/2006/vcard/ns#", const=True)


class DcatAPObject(BaseModel, ABC):
    """Base class for all DCAT-AP objects"""

    id_: str = Field(alias="@id")

    class Config:
        extra = Extra.forbid
        allow_population_by_field_name = True


class VCardIndividual(DcatAPObject):
    type_: str = Field(default="vcard:Individual", alias="@type", const=True)
    fn: str = Field(
        alias="vcard:fn", description="The formatted text corresponding to the name of the object"
    )


class VCardOrganisation(DcatAPObject):
    type_: str = Field(default="vcard:Organisation", alias="@type", const=True)
    fn: str = Field(
        alias="vcard:fn", description="The formatted text corresponding to the name of the object"
    )


class DcatLocation(DcatAPObject):
    type_: str = Field(default="dct:Location", alias="@type", const=True)
    bounding_box: str = Field(alias="dcat:bbox", default=None)
    centroid: str = Field(alias="dcat:centroid", default=None)
    geometry: str = Field(alias="dcat:geometry", default=None)


class SpdxChecksum(DcatAPObject):
    type_: str = Field(default="spdx:Checksum", alias="@type", const=True)
    algorithm: str = Field()
    checksumValue: str = Field()


class XSDDateTime(BaseModel):
    type_: str = Field(default="xsd:dateTime", alias="@type", const=True)
    value_: datetime.datetime | datetime.date = Field(alias="@value")

    class Config:
        extra = Extra.forbid
        allow_population_by_field_name = True


class DctPeriodOfTime(DcatAPObject):
    type_: str = Field(default="dct:PeriodOfTime", alias="@type", const=True)
    start_date: XSDDateTime | None = Field(alias="dcat:startDate", default=None)
    end_date: XSDDateTime | None = Field(alias="dcat:endDate", default=None)


class DcatAPIdentifier(DcatAPObject):
    """Identifying another DcatAPObject. Contains only an id."""


class DcatAPDistribution(DcatAPObject):
    type_: str = Field(default="dcat:Distribution", alias="@type", const=True)
    access_url: str = Field(alias="dcat:accessURL", default=None)
    byte_size: int | None = Field(alias="dcat:byteSize", default=None)
    checksum: DcatAPIdentifier | None = Field(alias="spdx:checksum", default=None)
    description: str | None = Field(alias="dct:description", default=None)
    download_url: str | None = Field(alias="dcat:downloadURL", default=None)
    format: str | None = Field(alias="dct:format", default=None)
    license: str | None = Field(alias="dct:license", default=None)
    title: str | None = Field(alias="dct:title", default=None)


class DcatAPDataset(DcatAPObject):
    type_: str = Field(default="dcat:Dataset", alias="@type", const=True)
    description: str | None = Field(
        alias="dct:description",
        description="This property contains a free-text account of the Dataset",
    )
    title: str = Field(
        alias="dct:title",
        description="This property contains a name given to the Dataset",
    )
    contact_point: list[DcatAPIdentifier] = Field(
        alias="dcat:contactPoint",
        description="This property contains contact information that can be used for sending "
        "comments about the Dataset.",
        default_factory=list,
    )
    distribution: list[DcatAPIdentifier] = Field(alias="dcat:distribution", default_factory=list)
    keyword: list[str] = Field(alias="dcat:keyword", default_factory=list)
    publisher: DcatAPIdentifier | None = Field(
        alias="dct:publisher",
        description="This property refers to an entity (organisation) responsible for making the "
        "Dataset available.",
    )

    creator: list[DcatAPIdentifier] = Field(alias="dcat:creator", default_factory=list)
    documentation: list[str] = Field(alias="foaf:page", default_factory=list)
    landing_page: list[str] = Field(
        alias="dcat:landingPage",
        description="This property refers to a web page that provides access to the Dataset, "
        "its Distributions and/or additional information. It is intended to point to "
        "a landing page at the original data provider, not to a page on a site of a "
        "third party, such as an aggregator.",
        default_factory=list,
    )
    release_date: XSDDateTime | None = Field(alias="dct:issued")
    update_date: XSDDateTime | None = Field(alias="dct:modified")
    version: str | None = Field(alias="owl:versionInfo")


class DcatApWrapper(BaseModel):
    """The resulting class, containing a dataset and related entities in the graph"""

    context_: DcatAPContext = Field(default=DcatAPContext(), alias="@context", const=True)
    # instead of list[DcatAPObject], a union with all the possible values is necessary. See
    # https://stackoverflow.com/questions/58301364/pydantic-and-subclasses-of-abstract-class
    graph_: list[
        Union[
            DcatAPDataset,
            DcatAPDistribution,
            DcatLocation,
            SpdxChecksum,
            VCardOrganisation,
            VCardIndividual,
            DctPeriodOfTime,
        ]
    ] = Field(alias="@graph")

    class Config:
        extra = Extra.forbid
        allow_population_by_field_name = True
