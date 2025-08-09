# Releasing and Versioning

The project loosely uses [Semantic Versions](https://semver.org) where the patch/micro number matches the release date.

## Breaking changes

!!! note "Work in Progress"

    Guidelines in "Breaking Changes" are the desired workflow, but in practice we are not always following them
    as 1) the metadata model wasn't yet matured and 2) the infrastructure for this needs to be
    developed. For now, we make sure all URLs are at least under a version suffix, which makes
    support in the future possible.

Breaking changes of a resource include deleting a field, changing the name of an existing field,
or changing the datatype of a field. Adding new fields is not a breaking change.

On a breaking change for a resource (e.g. for Dataset), a new router with a new version should
be created. The existing router should be deprecated, and rewritten so that it can handle the
new metadata of the database. This deprecation of a router will be visible in the Swagger
documentation. Calls to a deprecated router will still work, but a response header "Deprecated"
will be added with the deprecation date. The deprecated router will then be deleted on the next
release.

On non-breaking changes of a resource, a new version is not needed for the corresponding router.

Example:
- Start www.aiod.eu/api/datasets/v0
- Release 1: www.aiod.eu/api/datasets/v0 (no breaking changes)
- Release 2:
    - www.aiod.eu/api/datasets/v0 (deprecated)
    - www.aiod.eu/api/datasets/v1
- Release 3: www.aiod.eu/api/datasets/v1

## Changelog

As changelog we use the Github tags. For each release, a release branch should be created with a
bumped version in the pyproject.toml, and merged with the master. The tag should contain a
message detailing all the breaking and non-breaking changes. This message should adhere to the
guiding principles as described in https://keepachangelog.com/.

- Show all tags: https://github.com/aiondemand/AIOD-rest-api/tags
- Show a specific tag: https://github.com/aiondemand/AIOD-rest-api/releases/tag/0.3.20220501

This information can also be extracted using the Github REST API.


## Creating a release
To create a new release:

1. Make sure all requested functionality is merged with the `develop` branch.
2. Create a release branch from develop: `git checkout -b release/[VERSION]`. Example of version: `1.1.20231129`
3. Update the version in `pyproject.toml` on the release branch.
4. Test all (most of) the functionality. Checkout the project in a new directory and remove all
   your local images, and make sure it works out-of-the box.
5. Go to https://github.com/aiondemand/AIOD-rest-api/releases and draft a new release from the
   release branch. Look at all closed PRs and create a changelog.
6. Create a PR from release branch to develop. Make sure that when it is merged, the release branch is preserved.
7. Deploy on the server(s):
    - Check which services currently work (before the update). It's a sanity check for if a service _doesn't_ work later.
    - Bring the services down.
    - Update the code on the server by checking out the release.
    - If the release contains new configuration options or configuration defaults, make sure that the override files are updated as needed.
    - Start the services without connectors.
    - Make sure the latest database migrations are applied: see ["Schema Migrations"](schema/migration.md#update-the-database)
    - Restart the services with connectors.
9. Notify everyone (e.g., in the API channel in Slack).
