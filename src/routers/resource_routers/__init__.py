from versioning import Version
from .case_study_router import case_study_routers, CaseStudyRouter
from .computational_asset_router import ComputationalAssetRouter, computational_asset_routers
from .contact_router import ContactRouter, contact_routers
from .dataset_router import DatasetRouter, dataset_routers
from .educational_resource_router import EducationalResourceRouter, educational_resource_routers
from .event_router import EventRouter, event_routers
from .experiment_router import ExperimentRouter, experiment_routers
from .ml_model_router import MLModelRouter, ml_model_routers
from .news_router import NewsRouter, news_routers
from .organisation_router import OrganisationRouter, organisation_routers
from .person_router import PersonRouter, person_routers
from .platform_router import PlatformRouter
from .project_router import ProjectRouter, project_routers
from .publication_router import PublicationRouter, publication_routers
from .service_router import ServiceRouter, service_routers
from .team_router import TeamRouter, team_routers
from .resource_bundle_router import ResourceBundleRouter, resource_bundle_routers
from .. import ResourceRouter

all_routers = [value for attr, value in locals().items() if attr.endswith("_routers")]

router_list: list[ResourceRouter | PlatformRouter] = [
    PlatformRouter(),
]

versioned_routers = {
    version: [routers.get(version) for routers in all_routers] for version in Version
}
