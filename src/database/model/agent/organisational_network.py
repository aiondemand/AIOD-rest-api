from database.model.agent.agent import Agent, AgentBase
from versioning import Version, VersionedResource, VersionedResourceCollection


class OrganisationalNetworkBase(AgentBase):
    pass


class OrganisationalNetwork(OrganisationalNetworkBase, Agent, table=True):  # type: ignore
    __tablename__ = "organisational_network"
    __abbreviation__ = "net"
    __plural__ = "organisational_networks"

    class RelationshipConfig(Agent.RelationshipConfig):
        pass


organisational_network_versions = VersionedResourceCollection(
    {
        Version.LATEST: VersionedResource(OrganisationalNetwork),
        Version.V3: VersionedResource(OrganisationalNetwork),
    }
)
