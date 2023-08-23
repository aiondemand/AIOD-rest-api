import logging
from datetime import datetime
from typing import Iterator

import xmltodict
from sickle import Sickle

from connectors import ResourceConnector
from database.model.dataset.dataset import Dataset
from database.model.platform.platform_names import PlatformName

DATE_FORMAT = "%Y-%m-%d"


class ZenodoDatasetConnector(ResourceConnector[Dataset]):
    @property
    def resource_class(self) -> type[Dataset]:
        return Dataset

    @property
    def platform_name(self) -> PlatformName:
        return PlatformName.zenodo

    def _get_record_dictionary(self, record):
        xml_string = record.raw
        xml_dict = xmltodict.parse(xml_string)
        id = xml_dict["record"]["header"]["identifier"]
        if id.startswith("oai:"):
            id = id.replace("oai:", "")
        resource = xml_dict["record"]["metadata"]["oai_datacite"]["payload"]["resource"]
        return id, resource

    def _bad_record_format(self, dataset_id, field):
        logging.error(
            f"Error while fetching record info for dataset {dataset_id}: bad format {field}"
        )

    def _dataset_from_record(self, record_raw) -> Dataset | None:
        id_, record = self._get_record_dictionary(record_raw)
        if isinstance(record["creators"]["creator"], list):
            creators_list = [item["creatorName"] for item in record["creators"]["creator"]]
            creator = "; ".join(creators_list)  # TODO change field to an array
        elif isinstance(record["creators"]["creator"]["creatorName"], str):
            creator = record["creators"]["creator"]["creatorName"]
        else:
            self._bad_record_format(id_, "creator")
            return None

        if isinstance(record["titles"]["title"], str):
            title = record["titles"]["title"]
        else:
            self._bad_record_format(id_, "title")
            return None
        number_str = id_.rsplit("/", 1)[-1]
        idNumber = "".join(filter(str.isdigit, number_str))
        same_as = f"https://zenodo.org/api/records/{idNumber}"

        description_raw = record["descriptions"]["description"]
        if isinstance(description_raw, list):
            (description,) = [
                e.get("#text") for e in description_raw if e.get("@descriptionType") == "Abstract"
            ]
        elif description_raw["@descriptionType"] == "Abstract":
            description = description_raw["#text"]
        else:
            self._bad_record_format(id_, "description")
            return None

        date_published = None
        date_raw = record["dates"]["date"]
        if isinstance(date_raw, list):
            (description,) = [e.get("#text") for e in date_raw if e.get("@dateType") == "Issued"]
        elif date_raw["@dateType"] == "Issued":
            date_string = date_raw["#text"]
            date_published = datetime.strptime(date_string, DATE_FORMAT)
        else:
            self._bad_record_format(id_, "date_published")
            return None

        if isinstance(record["publisher"], str):
            publisher = record["publisher"]
        else:
            self._bad_record_format(id_, "publisher")
            return None

        if isinstance(record["rightsList"]["rights"], list):
            license_ = record["rightsList"]["rights"][0]["@rightsURI"]
        elif isinstance(record["rightsList"]["rights"]["@rightsURI"], str):
            license_ = record["rightsList"]["rights"]["@rightsURI"]
        else:
            self._bad_record_format(id_, "license")
            return None

        keywords = []
        if "subjects" in record:
            if isinstance(record["subjects"]["subject"], str):
                keywords = [record["subjects"]["subject"]]
            elif isinstance(record["subjects"]["subject"], list):
                keywords = [item for item in record["subjects"]["subject"] if isinstance(item, str)]
            else:
                self._bad_record_format(id_, "keywords")
                return None

        if license_ is None and keywords is None:
            keywords = license_  # making flake8 happy
        dataset = Dataset(
            platform="zenodo",
            platform_identifier=id_,
            name=title[:150],
            same_as=same_as,
            creator=creator[
                :150
            ],  # TODO not enough characters for creator list, change to array or allow more length
            description=description[:500],
            date_published=date_published,
            publisher=publisher,
            # license=LicenseOld(name=license_) if license_ is not None else None,
            # keywords=[KeywordOld(name=k) for k in keywords],
        )
        return dataset

    def _get_resource_type(self, record):
        xml_string = record.raw
        start = xml_string.find('<resourceType resourceTypeGeneral="')
        if start != -1:
            start += len('<resourceType resourceTypeGeneral="')
            end = xml_string.find('"', start)
            if end != -1:
                return xml_string[start:end]
        id_, _ = self._get_record_dictionary(record)
        logging.error(f"Error while getting the resource type of the record {id_}")
        return None

    def _retrieve_dataset_from_datetime(
        self,
        sk: Sickle,
        dt: datetime,
        limit: int | None = None,
    ) -> Iterator[Dataset]:
        records = sk.ListRecords(
            **{
                "metadataPrefix": "oai_datacite",
                "from": dt.isoformat(),
            }
        )
        counter = 0
        record = next(records, None)
        while record and (limit is None or counter < limit):
            if self._get_resource_type(record) == "Dataset":
                dataset = self._dataset_from_record(record)
                if dataset is not None:
                    counter += 1
                    yield dataset
            record = next(records, None)

    def fetch_all(self, limit: int | None = None) -> Iterator[Dataset]:
        sickle = Sickle("https://zenodo.org/oai2d")
        date = datetime(2000, 1, 1, 12, 0, 0)  # this should be a paramater
        return self._retrieve_dataset_from_datetime(sickle, date, limit)
