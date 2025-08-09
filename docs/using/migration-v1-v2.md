# Migration Guide


This is the migration guide for migrating from version 1 to version 2 of the AI-on-Demand REST API.
We provide some context for these changes, and provide concrete advice on what to change.
The current API is planned to sunset June 10th (may change, but never earlier).

## Changes for API v2 Versioning of the REST API

Previously, versions would be specified at the concept level, for example:

```
   https://api.aiod.eu/datasets/v1/24
```

This indicated you wanted dataset metadata in the schema of version 1 (`v1`).
This can be confusing when you have requests that provide mixed results, such as the endpoints to retrieve generic AI resources
(for example, `https://api.aiod.eu/ai_resources/v1/1`).
Instead, we will start versioning the catalogue as a whole.
For this reason, we are moving the location version identifier to the start to more explicitly signal it is API-wide, for example:

```
   https://api.aiod.eu/v2/datasets/24
```

Additionally, we now also provide an unversioned endpoint that always fetches the latest schema:

```
   https://api.aiod.eu/datasets/24
```

Here are some other examples:

| Old URL                | New Versioned URL      | Latest Version      |
|------------------------|------------------------|---------------------|
| /ai_resources/v1/1     | /v2/ai_resources/1     | /ai_resources/1     |
| /counts/v1             | /v2/counts             | /counts             |
| /datasets/v1/1/content | /v2/datasets/1/content | /datasets/1/content |
| /search/events/v1      | /v2/search/events      | /search/events      |
| /user/resources/v1     | /v2/user/resources     | /user/resources     |

So you need to update the URL to either the new v2 url (e.g., `/v2/datasets`) or the unversioned URL (e.g., `/datasets`).
Which you pick is up to you. Here are some considerations:

 - The versioned endpoints will work exactly the same way as long as they are available. There will be no breaking changes.
 - The versioned endpoints will eventually be deprecated when we need to make breaking changes to the API.
   We will employ a deprecation cycle and you will need to update the script in that time or otherwise it will stop working, even if the breaking changes that caused the version bump do not affect your script.
 - The unversioned endpoint doesn’t sunset. As long as your script is compatible, and remains compatible with the latest schema (for example, because the schema did not change), your code will continue to work.
 - The unversioned endpoint may change at any time without warning (for a new release), so your script may also suddenly stop working. At that point, you could pin it to the previous version and work on supporting the latest version again.

You could also consider using both endpoints, for example using the unversioned endpoint and falling back to a versioned endpoint if your requests fail.

## Identifiers of the assets on the platform

!!! warning "Important"

    This only applies if you have saved identifiers of assets somewhere.
    If you do not store identifiers, you can safely ignore this section.

When you fetch assets on the metadata catalogue, you will find multiple identifiers in their descriptions, for example:

```json
{
    "platform": "huggingface",
    "platform_resource_identifier": "621ffdd236468d709f181d6f",
    "name": "bigIR/ar_cov19",
    "ai_asset_identifier": 53,
    "ai_resource_identifier": 63,
    "identifier": 24,
     …
  },
```

Having different identifiers can lead to confusing situations.
Identifiers are frequently used to establish relationships between assets
(e.g., this dataset is related to that publication, or this person is a member of that organisation).
However, depending on the nature of the relationship, you would need to use a different identifier.
This is error-prone and may lead to users accidentally linking the wrong assets.

To address this issue, we are unifying the identifiers to make sure that every asset in the metadata catalogue has one single unique identifier for the AI-on-Demand platform. For example:

```json
{
    "platform": "huggingface",
    "platform_resource_identifier": "621ffdd236468d709f181d6f",
    "name": "bigIR/ar_cov19",
    "ai_asset_identifier": 63,    # instead of 53
    "ai_resource_identifier": 63, # remained the same
    "identifier": 63,             # instead of 24
     …
  },
```

In this example, referring to the dataset within AI-on-Demand always uses identifier ‘63’.
The only identifier we do not update, is the ‘platform_resource_identifier’, as that specifies where to find the original resource the metadata describes.
This identifier is never used internally within AI-on-Demand for linking assets, and so is not subject to accidental misuse described above.

If you have stored identifiers, you can find tables which map the old identifiers to the new identifiers here: (link to be added)

For technical reasons, we cannot support a transitional period where both identifiers are compatible with the API.
We plan to migrate to the new identifiers on June 11th.
So if you access assets using identifiers after that date, make sure to convert them first or you will likely receive the wrong assets or errors.

### Why is the no deprecation cycle for the change to identifiers?

While we provide a migration period for the URLs, we cannot provide one for the migration of identifiers.
Allowing both identifiers to be used in a transitional period adds a lot of complexity and possibilities for errors when linking assets.
Most crucially, there may be cases when a user wants to link assets by identifiers where we cannot tell if they are using old identifiers or new identifiers.
While we can support them under different endpoints, there is no way for use to ensure a user does not (accidentally) link assets referencing old identifiers on a new endpoint, or vice versa.
Maintaining the integrity of the data in the metadata catalogue is our highest priority, and so we decided that unfortunately we cannot support a grace period.
We hope for your understanding and will do our best to avoid such a scenario in the future.
