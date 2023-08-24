"""
Schema.org Dataset is an industry standard to describe Dataset Metadata. Founded by Google,
Microsoft, Yahoo and Yandex, Schema.org vocabularies are developed by an open community process.
See https://schema.org/Dataset.

Using pydantic_schemaorg was not possible. Swagger does not play nicely with the circular
references present in the schema.
"""
import datetime

from pydantic import BaseModel, Field, Extra


class SchemaDotOrgContext(BaseModel):
    vocab_: str = Field(default="http://schema.org/", alias="@vocab", constant=True)


class SchemaDotOrgDataDownload(BaseModel):
    """A dataset in downloadable form.

    See: https://schema.org/DataDownload
    """

    type_: str = Field(default="DataDownload", alias="@type", constant=True)
    name: str | None = Field(description="The name of the item.")
    contentUrl: str = Field(
        description="Actual bytes of the media object, for example the image file or video file.",
    )
    contentSize: str | None = Field(
        default=None,
        description="File size in (mega/kilo) bytes.",
    )
    encodingFormat: str | None = Field(
        default=None,
        description="Media type typically expressed using a MIME format (see "
        "[IANA site](http://www.iana.org/assignments/media-types/media-types.xhtml) and "
        "[MDN reference]("
        "https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types))"
        "e.g. application/zip for a SoftwareApplication binary, audio/mpeg for .mp3 etc.)."
        "In cases where a [[CreativeWork]] has several media type representations, [[encoding]]"
        "can be used to indicate each [[MediaObject]] alongside particular [[encodingFormat]]"
        "information. Unregistered or niche encoding and file formats can be indicated instead"
        "via the most appropriate URL, e.g. defining Web page or a Wikipedia/Wikidata entry.",
    )


class SchemaDotOrgOrganization(BaseModel):
    """An organization such as a school, NGO, corporation, club, etc.

    See: https://schema.org/Organization
    """

    type_: str = Field(default="Organization", alias="@type", constant=True)
    name: str = Field(description="The name of the item.")


class SchemaDotOrgPerson(BaseModel):
    """A person (alive, dead, undead, or fictional).

    See: https://schema.org/Person
    """

    type_: str = Field(default="Person", alias="@type", constant=True)
    name: str = Field(description="The name of the item.")
    givenName: str | None = Field(
        description="Given name. In the U.S., the first name of a Person."
    )
    familyName: str | None = Field(
        description="Family name. In the U.S., the last name of a Person."
    )


class SchemaDotOrgDataset(BaseModel):
    context_: SchemaDotOrgContext = Field(
        default=SchemaDotOrgContext(), alias="@context", constant=True
    )
    type_: str = Field(default="Dataset", alias="@type", constant=True)

    name: str = Field(description="The name of the item.")
    description: str = Field(default=None, description="A description of the item.")
    identifier: str = Field(description="The AIoD identifier")
    alternateName: list[str] | str | None = Field(
        default=None,
        description="An alias for the item.",
    )
    citation: list[str] | str | None = Field(
        default=None,
        description="A reference to another creative work, such as another publication, web page,"
        "scholarly article, etc.",
    )
    creator: list[
        SchemaDotOrgOrganization | SchemaDotOrgPerson
    ] | SchemaDotOrgOrganization | SchemaDotOrgPerson | None = Field(
        default=None,
        description="The creator/author of this CreativeWork. This is the same as the Author "
        "property for CreativeWork.",
    )
    dateModified: datetime.datetime | datetime.date = Field(
        default=None,
        description="The date on which the CreativeWork was most recently modified or when the "
        "item's entry was modified within a DataFeed.",
    )
    datePublished: datetime.datetime | datetime.date = Field(
        default=None,
        description="Date of first broadcast/publication.",
    )
    isAccessibleForFree: bool = Field(
        default=True,
        const=True,
        description="A flag to signal that the item, event, or place is accessible for free.",
    )
    keywords: list[str] | str | None = Field(
        default=None,
        description="Keywords or tags used to describe this content. Multiple entries in a "
        "keywords list are typically delimited by commas.",
    )
    sameAs: str | None = Field(
        default=None,
        description="URL of a reference Web page that unambiguously indicates the item's identity. "
        "E.g. the URL of the item's Wikipedia page, Wikidata entry, or official "
        "website.",
    )

    version: str | None = Field(
        default=None,
        description="The version of the CreativeWork embodied by a specified resource.",
    )
    url: str | None = Field(default=None, description="URL of the item.")

    distribution: SchemaDotOrgDataDownload | list[SchemaDotOrgDataDownload] | None = Field(
        default=None,
        description="A downloadable form of this dataset, at a specific location, in a specific "
        "format.",
    )

    funder: list[
        SchemaDotOrgOrganization | SchemaDotOrgPerson
    ] | SchemaDotOrgOrganization | SchemaDotOrgPerson | None = Field(
        default=None,
        description="A person or organization that supports (sponsors) something through some kind "
        "of financial"
        "contribution.",
    )
    issn: str | list[str] | None = Field(
        default=None,
        description="The International Standard Serial Number (ISSN) that identifies this serial "
        "publication. You can repeat this property to identify different formats of, or the "
        "linking ISSN (ISSN-L) for, this serial publication.",
    )
    license: list[str] | str = Field(
        default=None,
        description="A license document that applies to this content, typically indicated by URL.",
    )
    measurementTechnique: str | list[str] | None = Field(
        default=None,
        description="A technique or technology used in a [[Dataset]] (or [[DataDownload]], "
        "[[DataCatalog]]), corresponding to the method used for measuring the corresponding "
        "variable(s) (described using [[variableMeasured]]). This is oriented towards scientific "
        "and scholarly dataset publication but may have broader applicability; it is not intended "
        "as a full representation of measurement, but rather as a high level summary for dataset "
        "discovery. For example, if [[variableMeasured]] is: molecule concentration, "
        '[[measurementTechnique]] could be: "mass spectrometry" or "nmr spectroscopy" or '
        '"colorimetry" or "immunofluorescence". If the [[variableMeasured]] is "depression '
        'rating", the [[measurementTechnique]] could be "Zung Scale" or "HAM-D" or "Beck '
        'Depression Inventory". If there are several [[variableMeasured]] properties recorded for '
        "some given data object, use a [[PropertyValue]] for each [[variableMeasured]] and attach "
        "the corresponding [[measurementTechnique]].",
    )
    size: str | None = Field(
        default=None,
        description="A standardized size of a product or creative work, specified either through a "
        "simple textual string (for example 'XL', '32Wx34L'), a QuantitativeValue "
        "with a unitCode,",
    )
    temporalCoverage: datetime.datetime | str | None = Field(
        default=None,
        description="The temporalCoverage of a CreativeWork indicates the period that the content "
        "applies to, i.e. that it describes, either as a DateTime or as a textual string "
        "indicating a time period in [ISO 8601 time interval format]("
        "https://en.wikipedia.org/wiki/ISO_8601#Time_intervals)."
        "In the case of a Dataset it will typically indicate the relevant time period in a precise "
        'notation (e.g. for a 2011 census dataset, the year 2011 would be written "2011/2012"). '
        "Other forms of content e.g. ScholarlyArticle, Book, TVSeries or TVEpisode may indicate "
        "their temporalCoverage in broader terms - textually or via well-known URL. Written "
        "works such as books may sometimes have precise temporal coverage too, e.g. a work set "
        'in 1939 - 1945 can be indicated in ISO 8601 interval format format via "1939/1945". '
        'Open-ended date ranges can be written with ".." in place of the end date. For example, '
        '"2015-11/.." indicates a range beginning in November 2015 and with no specified final '
        "date. This is tentative and might be updated in future when ISO 8601 is officially "
        "updated.",
    )

    class Config:
        extra = Extra.forbid
