# Taxonomies

AI-on-Demand uses [taxonomies](https://en.wikipedia.org/wiki/Taxonomy) to standardize terms across assets, for example, for [licenses](https://aiod-dev.i3a.es/docs#/Taxonomies/license_licenses_get), [business sectors](https://aiod-dev.i3a.es/docs#/Taxonomies/industrial_sector_industrial_sectors_get), or [news categories](https://aiod-dev.i3a.es/docs#/Taxonomies/news_category_news_categorys_get).
These taxonomies are defined by the [conceptual model](https://github.com/aiondemand/metadata-schema).
Each term in a taxonomy has a specific definition and may have subterms defined. e.g., the business sector `construction` has subsectors for `infrastructure` and `buildings`, which each may also have subterms.

## Importing the Taxonomy
The JSON file produced by the export script in the metadata repository can be used as input for the `taxonomy` service of this project's `docker compose`.
Put the JSON file at `${DATA_PATH}/taxonomies/taxonomies.json`, where `DATA_PATH` is an environment variable (typically set from the `.env` file).
Then invoke docker compose with the "taxonomy" profile. The script will then:

 - invalidate all old known terms that are no longer part of the taxonomy: assets which already use them will keep them, but they may not be added to new items.
 - update existing terms, e.g., with new definitions
 - add new terms to the taxonomy

## Development Taxonomy
When using the development configuration, you put a file in the `${DATA_PATH}/taxonomies` directory and point to it from the API configuration file (`config.override.toml`), where `${DATA_PATH}/taxonomies` will be mounted as `/data/taxonomies`. For example, with `DATA_PATH=./data` and `./data/taxonomies/example_taxonomies.json` present:

```toml
[dev]
taxonomy="/data/taxonomies/example_taxonomies.json"
```

It is not intended to use this in production, since it might result in accidentally overwriting the taxonomies.
In production, use the `taxonomy` service discussed above.

## Other
As of [#565](https://github.com/aiondemand/AIOD-rest-api/pull/565), connectors are exempt from adhering to the taxonomies. This is currently planned to be only a temporary solution while we discuss how to move forward.
