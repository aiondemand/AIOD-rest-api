import re
from typing import Type

from sqlmodel import Session

from converters.schema.dcat import (
    DcatApWrapper,
    DcatAPDataset,
    VCardIndividual,
    DcatAPIdentifier,
    DcatAPDistribution,
    SpdxChecksum,
    DcatAPObject,
    XSDDateTime,
)
from converters.schema_converters.schema_converter import SchemaConverter
from database.model.dataset.dataset import Dataset


class DatasetConverterDcatAP(SchemaConverter[Dataset, DcatApWrapper]):
    """
    Convert an AIoD Dataset into a dcat-ap json-ld representation.
    """

    @property
    def to_class(self) -> Type[DcatApWrapper]:
        return DcatApWrapper

    def convert(self, session: Session, aiod: Dataset) -> DcatApWrapper:
        release_date = (
            XSDDateTime(value_=aiod.date_published) if aiod.date_published is not None else None
        )
        update_date = XSDDateTime(value_=aiod.aiod_entry.date_modified)
        dataset = DcatAPDataset(
            id_=aiod.identifier,
            description=aiod.description,
            title=aiod.name,
            keyword=[k.name for k in aiod.keyword],
            landing_page=[aiod.same_as] if aiod.same_as is not None else [],
            release_date=release_date,
            update_date=update_date,
            version=aiod.version,
        )
        graph: list[DcatAPObject] = [dataset]
        for person in aiod.contact:
            contact = VCardIndividual(
                id_=_replace_special_chars("individual_{}".format(person.name)), fn=person.name
            )
            graph.append(contact)
            dataset.contact_point = [DcatAPIdentifier(id_=contact.id_)]
        for person in aiod.creator:
            creator = VCardIndividual(
                id_=_replace_special_chars("individual_{}".format(person.name)), fn=person.name
            )
            if creator.id_ not in {obj.id_ for obj in graph}:
                graph.append(creator)
            dataset.creator = [DcatAPIdentifier(id_=creator.id_)]

        for aiod_distribution in aiod.distribution:
            checksum: SpdxChecksum | None = None

            if aiod_distribution.checksum is not None:
                checksum = SpdxChecksum(
                    id_=aiod_distribution.checksum,
                    algorithm=aiod_distribution.checksum_algorithm,
                    checksumValue=aiod_distribution.checksum,
                )
                graph.append(checksum)
            distribution = DcatAPDistribution(
                id_=aiod_distribution.content_url,
                title=aiod_distribution.name,
                access_url=aiod_distribution.content_url,
                checksum=DcatAPIdentifier(id_=checksum.id_) if checksum is not None else None,
                download_url=aiod_distribution.content_url,
                description=aiod_distribution.description,
                format=aiod_distribution.encoding_format,
                license=aiod.license.name if aiod.license is not None else None,
            )
            dataset.distribution.append(DcatAPIdentifier(id_=aiod_distribution.content_url))
            graph.append(distribution)
        return DcatApWrapper(graph_=graph)


def _replace_special_chars(name: str) -> str:
    """Replace special characters with underscores.

    Args:
        name: a name of a json-ld object.

    Returns:
        a sanitized version of the name
    """
    return re.sub("[^A-Za-z0-9]", "_", name)
