import pathlib

from connectors.example.example_connector import ExampleConnector
from database.model.agent.organisation import Organisation
from database.model.agent.person import Person
from database.model.agent.team import Team
from database.model.case_study.case_study import CaseStudy
from database.model.computational_asset.computational_asset import ComputationalAsset
from database.model.dataset.dataset import Dataset
from database.model.educational_resource.educational_resource import EducationalResource
from database.model.event.event import Event
from database.model.knowledge_asset.publication import Publication
from database.model.models_and_experiments.experiment import Experiment
from database.model.models_and_experiments.ml_model import MLModel
from database.model.news.news import News
from database.model.project.project import Project
from database.model.service.service import Service

RESOURCE_PATH = pathlib.Path(__file__).parent.parent / "example" / "resources" / "resource"


class ExampleCaseStudyConnector(ExampleConnector[CaseStudy]):
    def __init__(self):
        json_path = RESOURCE_PATH / "case_studies.json"
        super().__init__(json_path, CaseStudy)


class ExampleComputationalAssetConnector(ExampleConnector[ComputationalAsset]):
    def __init__(self):
        json_path = RESOURCE_PATH / "computational_assets.json"
        super().__init__(json_path, ComputationalAsset)


class ExampleDatasetConnector(ExampleConnector[Dataset]):
    def __init__(self):
        json_path = RESOURCE_PATH / "datasets.json"
        super().__init__(json_path, Dataset)


class ExampleEducationalResourceConnector(ExampleConnector[EducationalResource]):
    def __init__(self):
        json_path = RESOURCE_PATH / "educational_resources.json"
        super().__init__(json_path, EducationalResource)


class ExampleEventConnector(ExampleConnector[Event]):
    def __init__(self):
        json_path = RESOURCE_PATH / "events.json"
        super().__init__(json_path, Event)


class ExampleExperimentConnector(ExampleConnector[Experiment]):
    def __init__(self):
        json_path = RESOURCE_PATH / "experiments.json"
        super().__init__(json_path, Experiment)


class ExampleMLModelConnector(ExampleConnector[MLModel]):
    def __init__(self):
        json_path = RESOURCE_PATH / "ml_models.json"
        super().__init__(json_path, MLModel)


class ExampleNewsConnector(ExampleConnector[News]):
    def __init__(self):
        json_path = RESOURCE_PATH / "news.json"
        super().__init__(json_path, News)


class ExampleOrganisationConnector(ExampleConnector[Organisation]):
    def __init__(self):
        json_path = RESOURCE_PATH / "organisations.json"
        super().__init__(json_path, Organisation)


class ExamplePersonConnector(ExampleConnector[Person]):
    def __init__(self):
        json_path = RESOURCE_PATH / "persons.json"
        super().__init__(json_path, Person)


class ExampleProjectConnector(ExampleConnector[Project]):
    def __init__(self):
        json_path = RESOURCE_PATH / "projects.json"
        super().__init__(json_path, Project)


class ExamplePublicationConnector(ExampleConnector[Publication]):
    def __init__(self):
        json_path = RESOURCE_PATH / "publications.json"
        super().__init__(json_path, Publication)


class ExampleServiceConnector(ExampleConnector[Service]):
    def __init__(self):
        json_path = RESOURCE_PATH / "services.json"
        super().__init__(json_path, Service)


class ExampleTeamConnector(ExampleConnector[Team]):
    def __init__(self):
        json_path = RESOURCE_PATH / "teams.json"
        super().__init__(json_path, Team)
