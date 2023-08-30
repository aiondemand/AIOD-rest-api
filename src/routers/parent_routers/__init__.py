from .agent_router import AgentRouter
from .ai_asset_router import AIAssetRouter
from .ai_resource_router import AIResourceRouter
from ..parent_router import ParentRouter

router_list: list[ParentRouter] = [AgentRouter(), AIAssetRouter(), AIResourceRouter()]
