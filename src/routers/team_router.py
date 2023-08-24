from database.model.agent.team import Team
from routers.resource_router import ResourceRouter


class TeamRouter(ResourceRouter):
    @property
    def version(self) -> int:
        return 1

    @property
    def resource_name(self) -> str:
        return "team"

    @property
    def resource_name_plural(self) -> str:
        return "teams"

    @property
    def resource_class(self) -> type[Team]:
        return Team
