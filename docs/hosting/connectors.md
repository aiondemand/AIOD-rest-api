# Connectors for AI-on-Demand
[//]: # (The section below is referenced in "./docs/hosting/index.md", if you change lines in this block, update the reference accordingly.)

To start connector services that automatically index data from external platforms into the metadata catalogue,
you must specify their docker-compose profiles (as defined in the `docker-compose.yaml` file).
Their configuration, if any, is through environment variables which can be set in the `override.env` file as explained in ["Configuring the Metadata Catalogue"](index.md#configuration).
For example, you can use the following commands when starting the connectors for OpenML and Zenodo.

=== "Shorthand"

    ```commandline
    ./scripts/up.sh openml zenodo-datasets
    ```

=== "Docker Compose"

    ```commandline
    docker compose --profile openml --profile zenodo-datasets --env-file=.env --env-file=override.env up -d
    ```

!!! warning "Connectors and Syncing Nodes"

    If you are configuring your metadata catalogue as part of a [set of root nodes](synchronization.md),
    only one of the root nodes should be running the connectors. Running the same connector on
    multiple root nodes _may_ introduce conflicts.

The full list of connector profiles are:

- [aibuilder](connectors.md#ai-builder): indexes models on AI Builder
- [huggingface-datasets](connectors.md#huggingface): indexes datasets from Hugging Face.
- [openml](connectors.md#openml): indexes datasets and models from OpenML.
- [zenodo-datasets](connectors.md#zenodo): indexes datasets from Zenodo.
- [examples](connectors.md#examples): fills the database with some example data. **Do not use in production.**

[//]: # (The section above is referenced in "./docs/hosting/index.md", if you change lines in this block, update the reference accordingly.)

[//]: # (Connectors below in alphabetic order, except for examples, which is last.)

## AI Builder

**Profile**: `aibuilder`

Indexes models in the [AI Builder](https://aiexp.ai4europe.eu/#/home) library.
When running the AI Builder connector, you need to provide a valid API token through the `AIBUILDER_API_TOKEN` environment variable.

AI Builder's models are only accessible with authentication, and for this the API key is required to be part of the query in the URL.
Because we do not want to expose the API key, we obfuscate it and use `AIBUILDER_API_TOKEN` in URLs.
This means that for using the url of the `same_as` field of the AIBuilder models, you will need to substitute `AIBUILDER_API_TOKEN` on the url for your actual API token value.

Separately, you can configure the AI Builder API URL and the request timeout in `src/config.default.toml` (or `config.override.toml`):

```toml
[aibuilder]
api_url = "https://aiexp-dev.ai4europe.eu/federation"
request_timeout = 30 # seconds
```

## HuggingFace

**Profile**: `huggingface-datasets`

Indexes datasets in the [Hugging Face](https://www.huggingface.co) repository.

## OpenML

**Profile**: `openml`

Indexes datasets and models (OpenML flows) in the [OpenML](https://www.openml.org) repository.

## Zenodo

**Profile**: `zenodo-datasets`

Indexes datasets in the [Zenodo](https://www.zenodo.org) repository.

## Examples

**Profile**: `examples`

Adds example assets in many different categories to the database.
This connector is for development purposes only and should not be used in production.
