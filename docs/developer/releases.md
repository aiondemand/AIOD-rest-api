# Releasing and Versioning

The project loosely uses [Semantic Versions](https://semver.org) where the patch/micro number matches the release date.

## Breaking changes

!!! note "Work in Progress"

    Guidelines in "Breaking Changes" are the desired workflow, but in practice we are not always following them
    as 1) the metadata model wasn't yet matured and 2) the infrastructure for this needs to be
    developed. For now, we make sure all URLs are at least under a version suffix, which makes
    support in the future possible.

We do our best to version API changes such that users can opt out of breaking changes.
We consider the following breaking changes:

 - removing a field from the input
 - changing the name of a field
 - changing the datatype of a field
 - changing or removing the default of a field

We generally try to avoid putting breaking changes into already released versions.
There can be some exceptions based on the developers' judgement, but such a decision should not
be made lightly and clearly communicated. Once the project matures more, one should avoid these
changes altogether. Some changes may be backported in a compatible manner,
for example instead of changing the name for a field, you could add a field with the new name without removing the old one.
This gives people time to move from one name to the other ([example](https://github.com/aiondemand/AIOD-rest-api/pull/594)).

The entire API is versioned together. This is because of the interconnectedness of assets.
If one versioned asset types independently, but we return e.g., `Person`s that are member of an `Organisation`
as part of the organisations endpoint, we would need a way to specify versions for both `Organisation` and `Person`
in the request. Because there are many high-level connections (e.g., `has_part` and `is_part_of`) we felt it is
better to version the entire API. However, while we internally have *some* support for schema migrations (
[example](https://github.com/aiondemand/AIOD-rest-api/blob/ff24e3c4278194b405bc49adc93991704e9c0e1d/src/database/model/project/project.py#L122)
), there are still issues when they are retrieved through indirect means ([#633](https://github.com/aiondemand/AIOD-rest-api/issues/633)).

## Creating a release
To create a new release:

1. Make sure all requested functionality is merged with the `develop` branch.
2. Make sure the version in `pyproject.toml` is updated in the `develop` branch.
3. Make a release on GitHub: https://github.com/aiondemand/AIOD-rest-api/releases
4. Make sure the release notes follow a similar style, use the merged PRs since last release (use e.g. filter `merged:>=2025-08-2`).

Deploy the new release to the test server. If that works (preferably leave it up for a while), then deploy to production.
Deploying an update:

 1. Create an additional database backup: `./scripts/mysql_dump.sh`
 1. Check which services currently work (before the update). It's a sanity check for if a service _doesn't_ work later.
 1. See which files, if any, are changed locally: `git status`
   - Stash the changes, or keep track of them in some way. Try to make a note to update the software so that local changes are not necessary.
 1. Check out the release (e.g., `git fetch origin && git checkout v2.0.20250802`)
   - If absolutely necessary, reapply the changes. Again: make a note to avoid needing any local changes next time.
 1. If the release contains new configuration options or configuration defaults, make sure that the override files are updated as needed.
 1. Rebuild the images: `./scripts/build.sh`
 1. Build the alembic image separately (it's not included in the above script), see `docker build -f alembic/Dockerfile . -t aiod-migration` ([docs](schema/migration.md).
 1. Bring down the services: `./scripts/down.sh`
 1. Bring the database back up: `docker compose --env-file=.env --env-file=override.env up sqlserver -d`
-  Runs the [migrations](schema/migration.md), if any: `docker run -v $(pwd)/alembic:/alembic:ro  -v $(pwd)/src:/app -it --network aiod-rest-api_default  aiod-migration`
- Start the remainder of the services: `./scripts/up.sh`
- To make sure the latest taxonomy is also included:
  - Copy the `export/taxonomies.json` file from the `metadata-schema` repository and have it update on startup, or
  - run the taxonomy service independently (preferred, but currently broken?)
- Notify everyone (e.g., in the API channel in Slack).
