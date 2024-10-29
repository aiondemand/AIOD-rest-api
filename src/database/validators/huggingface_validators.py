from huggingface_hub.utils import validate_repo_id


def throw_error_on_invalid_identifier(platform_resource_identifier: str):
    """
    Throw a ValueError on an invalid repository identifier.

    Valid repo_ids:
        Between 1 and 96 characters.
        Either “repo_name” or “namespace/repo_name”
        [a-zA-Z0-9] or ”-”, ”_”, ”.”.
        The following sequences ”--” and ”..” are forbidden.

    Refer to:
    https://huggingface.co/docs/huggingface_hub/package_reference/utilities#huggingface_hub.utils.validate_repo_id
    """
    repo_id = platform_resource_identifier
    validate_repo_id(repo_id=repo_id)
