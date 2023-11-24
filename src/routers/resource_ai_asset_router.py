import requests
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response

from database.model.ai_asset.ai_asset import AIAsset
from .resource_router import ResourceRouter, _wrap_as_http_exception


class ResourceAIAssetRouter(ResourceRouter):
    def create(self, url_prefix: str) -> APIRouter:
        version = "v1"
        default_kwargs = {
            "response_model_exclude_none": True,
            "deprecated": False,
            "tags": [self.resource_name_plural],
        }

        router = super().create(url_prefix)

        router.add_api_route(
            path=f"{url_prefix}/{self.resource_name_plural}/{version}/{{identifier}}/content",
            endpoint=self.get_resource_content_func(default=True),
            name=self.resource_name,
            response_model=str,
            **default_kwargs,
        )

        router.add_api_route(
            path=f"{url_prefix}/{self.resource_name_plural}/{version}/{{identifier}}/content/"
            f"{{distribution_idx}}",
            endpoint=self.get_resource_content_func(default=False),
            name=self.resource_name,
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
            identifier: str,
            distribution_idx: int,
            default: bool = False,
        ):
            f"""Retrieve a distribution of the content for {self.resource_name}
            identified by its identifier."""

            metadata: AIAsset = self.get_resource(
                identifier=identifier, schema="aiod", platform=None
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
                        "at the end of the url for a especific distribution.",
                    ),
                )
            elif distribution_idx >= len(distributions):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Distribution index out of range.",
                )

            try:
                url = distributions[distribution_idx].content_url
                encoding_format = distributions[distribution_idx].encoding_format
                filename = distributions[distribution_idx].name

                response = requests.get(url)
                content = response.content
                headers = {
                    "Content-Disposition": (
                        "attachment; " f"filename={filename or url.split('/')[-1]}"
                    )
                }
                if encoding_format:
                    headers["Content-Type"] = encoding_format

                return Response(content=content, headers=headers)

            except Exception as exc:
                raise _wrap_as_http_exception(exc)

        def get_resource_content_default(identifier: str):
            f"""Retrieve the first distribution (index 0 as default) of the content
            for a {self.resource_name} identified by its identifier."""
            return get_resource_content(identifier=identifier, distribution_idx=0, default=True)

        if default:
            return get_resource_content_default

        return get_resource_content
