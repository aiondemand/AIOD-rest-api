from typing import Annotated

from fastapi import APIRouter, HTTPException, status, Path, Depends
from fastapi.responses import RedirectResponse

from authentication import get_user_or_none, KeycloakUser
from database.model.ai_asset.ai_asset import AIAsset
from .resource_router import ResourceRouter


class ResourceAIAssetRouter(ResourceRouter):
    def create(self, url_prefix: str) -> APIRouter:
        default_kwargs = {
            "response_model_exclude_none": True,
            "deprecated": False,
            "tags": [self.resource_name_plural],
        }

        router = super().create(url_prefix)

        for path in [
            f"{url_prefix}/v2/{self.resource_name_plural}/{{identifier}}/content",
            f"{url_prefix}/{self.resource_name_plural}/{{identifier}}/content",
        ]:
            router.add_api_route(
                path=path,
                endpoint=self.get_resource_content_func(default=True),
                name=self.resource_name,
                description="Retrieve the actual content of the first distribution (index 0 as "
                "default) for a {self.resource_name} identified by its identifier.",
                response_model=str,
                **default_kwargs,
            )

        for path in [
            f"{url_prefix}/v2/{self.resource_name_plural}/{{identifier}}/content/{{distribution_idx}}",
            f"{url_prefix}/{self.resource_name_plural}/{{identifier}}/content/{{distribution_idx}}",
        ]:
            router.add_api_route(
                path=path,
                endpoint=self.get_resource_content_func(default=False),
                name=self.resource_name,
                description=f"Retrieve the actual content of a distribution for a {self.resource_name} "
                "identified by its identifier.",
                response_model=str,
                **default_kwargs,
            )

        return router

    def get_resource_content_func(self, default: bool):
        """
        Returns a function to download the content from resources.
        This function returns a function (instead of being that function directly) because the
        docstring and the variables are dynamic, and used in Swagger.
        """

        def get_resource_content(
            identifier: Annotated[
                str, Path(description=f"The identifier of the {self.resource_name}")
            ],
            distribution_idx: Annotated[
                int,
                Path(description=f"The index of the distribution within the {self.resource_name}"),
            ],
            user: KeycloakUser | None = Depends(get_user_or_none),
        ):
            metadata: AIAsset = self.get_resource(
                identifier=identifier,
                schema="aiod",
                platform=None,
                user=user,
            )  # type: ignore

            distributions = metadata.distribution
            if not distributions:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Distribution not found."
                )
            elif default and (len(distributions) > 1):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        "Multiple distributions encountered. "
                        "Use another endpoint indicating the distribution index `distribution_idx` "
                        "at the end of the url for a specific distribution."
                    ),
                )
            elif distribution_idx >= len(distributions):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Distribution index out of range.",
                )
            url = distributions[distribution_idx].content_url

            return RedirectResponse(url=url, status_code=status.HTTP_303_SEE_OTHER)

        def get_resource_content_default(
            identifier: Annotated[
                str, Path(description=f"The identifier of the {self.resource_name}")
            ],
            user: KeycloakUser | None = Depends(get_user_or_none),
        ):
            return get_resource_content(identifier=identifier, distribution_idx=0, user=user)

        if default:
            return get_resource_content_default

        return get_resource_content
