import logging
import requests
import xmltodict

from datetime import datetime, timedelta, timezone
from ratelimit import limits, sleep_and_retry
from requests.exceptions import HTTPError
from sickle import Sickle
from sickle.iterator import BaseOAIIterator
from starlette import status
from typing import Iterator, Tuple

from config import REQUEST_TIMEOUT
from connectors.abstract.resource_connector_by_date import ResourceConnectorByDate
from connectors.record_error import RecordError
from connectors.resource_with_relations import ResourceWithRelations
from database.model import field_length
from database.model.agent.contact import Contact
from database.model.ai_asset.distribution import Distribution
from database.model.ai_resource.text import Text
from database.model.concept.aiod_entry import AIoDEntryCreate
from database.model.dataset.dataset import Dataset
from database.model.platform.platform_names import PlatformName
from database.model.resource_read_and_create import resource_create


DATE_FORMAT = "%Y-%m-%d"
HARVESTING_MAX_CALLS_PER_MIN = 120
GLOBAL_MAX_CALLS_MINUTE = 60
GLOBAL_MAX_CALLS_HOUR = 2000
ONE_MINUTE = 60
ONE_HOUR = 3600


class ZenodoDatasetConnector(ResourceConnectorByDate[Dataset]):
    @property
    def resource_class(self) -> type[Dataset]:
        return Dataset

    @property
    def platform_name(self) -> PlatformName:
        return PlatformName.zenodo

    def retry(self, _id: int) -> ResourceWithRelations[Dataset] | RecordError:
        """
        This function fetches only one record from Zenodo using the Rest API instead of
        the OAI-PMH one. When querying using the OAI protocol, we always receive all the
        records, making it really inefficient to filter through all of them until we get
        the one we want. Apart from using different protocols, they also employ different
        serialization methods. The Rest API uses JSON, while OAI uses XML, which is why the
        code shows no similarities.
        """

        raise NotImplementedError(
            "Currently not implemented. See git history for an earlier "
            "implementation, that needs to be brought up-to-date (ideally "
            "using the same code as fetch)."
        )

    @staticmethod
    def _error_msg_bad_format(field) -> str:
        return f"Error while fetching record info: bad format {field}"

    @staticmethod
    @sleep_and_retry
    @limits(calls=GLOBAL_MAX_CALLS_MINUTE, period=ONE_MINUTE)
    @limits(calls=GLOBAL_MAX_CALLS_HOUR, period=ONE_HOUR)
    def _get_record(id_number: str) -> requests.Response:
        response = requests.get(
            f"https://zenodo.org/api/records/{id_number}/files", timeout=REQUEST_TIMEOUT
        )
        return response

    def _dataset_from_record(
        self, identifier: str, record: dict
    ) -> ResourceWithRelations[Dataset] | RecordError:
        """
        Process the information from a dataset and calls the Zenodo API for further information.
        """
        error_fmt = ZenodoDatasetConnector._error_msg_bad_format
        creators_raw = record.get("creators", {}).get("creator")
        creator_names = None
        if isinstance(creators_raw, list):
            creator_names = [
                item.get("creatorName", {}).get("#text")
                for item in creators_raw
                if isinstance(item, dict)
            ]
            creator_names = None if None in creator_names else creator_names
        elif isinstance(creators_raw, dict) and isinstance(
            creators_raw.get("creatorName", {}).get("#text"), str
        ):
            creator_names = [creators_raw["creatorName"]["#text"]]
        if creator_names is None:
            return RecordError(identifier=identifier, error=error_fmt("creator"))

        creators = []
        pydantic_class_contact = resource_create(Contact)
        for name in creator_names:
            creators.append(pydantic_class_contact(name=name))

        titles_raw = record.get("titles", {}).get("title")
        # Checking only the str type, as it is expected that each dataset has a single title
        if isinstance(titles_raw, str):
            title = titles_raw
        else:
            return RecordError(identifier=identifier, error=error_fmt("title"))
        if len(title) > field_length.NORMAL:
            text_break = " [...]"
            title = title[: field_length.NORMAL - len(text_break)] + text_break

        number_str = identifier.rsplit("/", 1)[-1]
        id_number = "".join(filter(str.isdigit, number_str))
        same_as = f"https://zenodo.org/api/records/{id_number}"

        description = None
        description_raw = record.get("descriptions", {}).get("description")
        if isinstance(description_raw, list):
            description_list = [
                e.get("#text") for e in description_raw if e.get("@descriptionType") == "Abstract"
            ]
            description = description_list[0] if len(description_list) == 1 else None
        elif isinstance(description_raw, dict) and (
            description_raw.get("@descriptionType") == "Abstract"
        ):
            description = description_raw.get("#text")
        if description is None:
            return RecordError(identifier=identifier, error=error_fmt("description"))

        if len(description) > field_length.LONG:
            text_break = " [...]"
            description = description[: field_length.LONG - len(text_break)] + text_break
        if description:
            description = Text(plain=description)

        date_string = None
        date_raw = record.get("dates", {}).get("date")
        if isinstance(date_raw, list):
            date_list = [e.get("#text") for e in date_raw if e.get("@dateType") == "Issued"]
            date_string = date_list[0] if len(date_list) == 1 else None
        elif isinstance(date_raw, dict) and (date_raw.get("@dateType") == "Issued"):
            date_string = date_raw.get("#text", "")

        date_published = None
        if date_string is not None:
            try:
                date_published = datetime.strptime(date_string, DATE_FORMAT)
            except Exception:
                date_published = None
        if date_published is None:
            return RecordError(identifier=identifier, error=error_fmt("date_published"))

        publisher = None
        if "publisher" in record:
            if isinstance(record["publisher"], str):
                publisher = record["publisher"]
            else:
                return RecordError(identifier=identifier, error=error_fmt("publisher"))

        license_ = None
        if "rightsList" in record:
            rights_raw = record["rightsList"].get("rights")
            if isinstance(rights_raw, list):
                license_ = rights_raw[0].get("#text")
            elif isinstance(rights_raw, dict) and isinstance(rights_raw.get("#text"), str):
                license_ = rights_raw["#text"]
            else:
                return RecordError(identifier=identifier, error=error_fmt("license"))

        keywords = []
        if "subjects" in record:
            subjects_raw = record["subjects"].get("subject")
            if isinstance(subjects_raw, str):
                keywords = [subjects_raw]
            elif isinstance(subjects_raw, list):
                keywords = [item for item in subjects_raw if isinstance(item, str)]
            else:
                return RecordError(identifier=identifier, error=error_fmt("keywords"))

        response: requests.Response = self._get_record(id_number)

        if response.status_code == status.HTTP_200_OK:
            entries = response.json()["entries"]
            distributions = [
                Distribution(
                    name=entry["key"],
                    content_url=entry["links"]["content"],
                    encoding_format=entry["mimetype"],
                    checksum_algorithm=(
                        entry["checksum"].split(":")[0] if "checksum" in entry else None
                    ),
                    checksum=entry["checksum"].split(":")[1] if "checksum" in entry else None,
                )
                for entry in entries
            ]
        elif response.status_code in (status.HTTP_403_FORBIDDEN, status.HTTP_410_GONE):
            distributions = []  # Private files, or deleted files
        else:
            response.raise_for_status()

        pydantic_class = resource_create(Dataset)
        dataset = pydantic_class(
            aiod_entry=AIoDEntryCreate(status="published"),
            platform="zenodo",
            platform_resource_identifier=identifier,
            name=title,
            same_as=same_as,
            description=description,
            date_published=date_published,
            publisher=publisher,
            license=license_,
            keyword=keywords,
            distribution=distributions,
        )

        return ResourceWithRelations[pydantic_class](  # type:ignore
            resource=dataset, resource_ORM_class=Dataset, related_resources={"creator": creators}
        )

    @staticmethod
    def _resource_type(record) -> str | None:
        """Cheap check before parsing the complete XML."""
        xml_string = record.raw
        start = xml_string.find('<resourceType resourceTypeGeneral="')
        if start != -1:
            start += len('<resourceType resourceTypeGeneral="')
            end = xml_string.find('"', start)
            if end != -1:
                return xml_string[start:end]
        return None

    @staticmethod
    @sleep_and_retry
    @limits(calls=HARVESTING_MAX_CALLS_PER_MIN, period=ONE_MINUTE)
    def _check_harvesting_rate() -> None:
        pass

    def _fetch_record_list(self, records_iterator: BaseOAIIterator, batchsize: int) -> list:
        """
        Fetches the maximum number of records available before the resumption token expires.
        It also ensures that the harvesting limit rate is not exceeded.
        """
        resumption_token = records_iterator.resumption_token
        if resumption_token and resumption_token.expiration_date:
            expiration_date = datetime.fromisoformat(resumption_token.expiration_date) - timedelta(
                seconds=10
            )
        else:
            current_date_time = datetime.utcnow().replace(tzinfo=timezone.utc)
            expiration_date = current_date_time + timedelta(seconds=110)

        records_list = []
        i = 0
        try:
            for record in records_iterator:
                i += 1
                records_list.append(record)
                if batchsize and (i % batchsize) == 0:
                    now = datetime.utcnow().replace(tzinfo=timezone.utc)
                    if now >= expiration_date:
                        logging.info(f"Resumption token expired at {expiration_date}!")
                        break
                    self._check_harvesting_rate()
                    logging.info(f"{i} records retrieved")
        except HTTPError as exc:
            if (exc.response is not None) and (
                exc.response.status_code >= status.HTTP_400_BAD_REQUEST
            ):
                msg = (
                    f"Failed to fetch new records. Zenodo returned {exc.response.reason} "
                    f"with status code ({exc.response.status_code})!"
                )
                msg += " Processing the acquired records..." if i > 0 else ""
                logging.info(msg)
            else:
                raise exc

        return records_list

    def fetch(
        self, from_incl: datetime, to_excl: datetime
    ) -> Iterator[Tuple[datetime | None, Dataset | ResourceWithRelations[Dataset] | RecordError]]:
        """
        First it fetches all the records and then it process all of them.
        This way, it ensures to retrieve the maximum number of available records before the
        resumption token expires.
        """
        self.is_concluded = False

        self._check_harvesting_rate()
        logging.info("Retrieving records from Zenodo...")
        sickle = Sickle("https://zenodo.org/oai2d")
        try:
            records_iterator = sickle.ListRecords(
                **{
                    "metadataPrefix": "oai_datacite",
                    "from": from_incl.replace(tzinfo=None).isoformat(),
                    "until": to_excl.replace(tzinfo=None).isoformat(),
                }
            )
        except HTTPError as err:
            if err.response is not None and (
                err.response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            ):
                self.is_concluded = True
                yield None, RecordError(identifier=None, error=err)
                return
            else:
                raise err

        oai_response_dict = xmltodict.parse(records_iterator.oai_response.raw)
        raw_records = oai_response_dict.get("OAI-PMH", {}).get("ListRecords", {}).get("record", [])
        batchsize = len(raw_records)

        complete_list_size = (
            int(records_iterator.resumption_token.complete_list_size)
            if records_iterator.resumption_token
            and records_iterator.resumption_token.complete_list_size
            else batchsize
        )

        records = self._fetch_record_list(records_iterator, batchsize)
        logging.info(f"{len(records)} records retrieved out of {complete_list_size}")

        i = 0
        for record in records:
            processed_record: ResourceWithRelations[Dataset] | RecordError
            i += 1
            id_ = None
            datetime_: datetime | None = None
            resource_type = ZenodoDatasetConnector._resource_type(record)
            if resource_type is None:
                processed_record = RecordError(
                    identifier=id_, error="Resource type could not be determined"
                )
            else:
                try:
                    xml_string = record.raw
                    xml_dict = xmltodict.parse(xml_string)
                    id_ = xml_dict["record"]["header"]["identifier"]
                    if id_.startswith("oai:"):
                        id_ = id_.replace("oai:", "")

                    datetime_ = datetime.fromisoformat(xml_dict["record"]["header"]["datestamp"])
                    if resource_type == "Dataset":
                        resource = xml_dict["record"]["metadata"]["oai_datacite"]["payload"][
                            "resource"
                        ]
                        processed_record = self._dataset_from_record(id_, resource)
                    else:
                        processed_record = RecordError(
                            identifier=id_, error="Wrong type", ignore=True
                        )
                except Exception as e:
                    processed_record = RecordError(identifier=id_, error=e)

            self.is_concluded = i == complete_list_size
            yield datetime_, processed_record
