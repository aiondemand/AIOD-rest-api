from database.model.agent.team import Team, team_versions
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


team_routers = {
    version: TeamRouter(versioned_resource) for version, versioned_resource in team_versions.items()
}
