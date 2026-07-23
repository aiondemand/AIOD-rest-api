from versioning import Version
from .case_study_router import case_study_routers, CaseStudyRouter  # noqa: F401
from .computational_asset_router import ComputationalAssetRouter, computational_asset_routers  # noqa: F401
from .contact_router import ContactRouter, contact_routers  # noqa: F401
from .dataset_router import DatasetRouter, dataset_routers  # noqa: F401
from .educational_resource_router import EducationalResourceRouter, educational_resource_routers  # noqa: F401
from .event_router import EventRouter, event_routers  # noqa: F401
from .experiment_router import ExperimentRouter, experiment_routers  # noqa: F401
from .ml_model_router import MLModelRouter, ml_model_routers  # noqa: F401
from .news_router import NewsRouter, news_routers  # noqa: F401
from .organisation_router import OrganisationRouter, organisation_routers  # noqa: F401
from .person_router import PersonRouter, person_routers  # noqa: F401
from .platform_router import PlatformRouter
from .project_router import ProjectRouter, project_routers  # noqa: F401
from .publication_router import PublicationRouter, publication_routers  # noqa: F401
from .service_router import ServiceRouter, service_routers  # noqa: F401
from .team_router import TeamRouter, team_routers  # noqa: F401
from .resource_bundle_router import ResourceBundleRouter, resource_bundle_routers  # noqa: F401
from .. import ResourceRouter

all_routers = [value for attr, value in locals().items() if attr.endswith("_routers")]

router_list: list[ResourceRouter | PlatformRouter] = [
    PlatformRouter(),
]

versioned_routers = {
    version: [routers.get(version) for routers in all_routers] for version in Version
}
