# Hosting the Metadata Catalogue
This page has information on how to host your own metadata catalogue.
If you plan to locally develop the REST API, please follow the installation procedure in ["Contributing"](../contributing) instead.

## Prerequisites
The platform is tested on Linux, but should also work on Windows and MacOS.
Additionally, it needs [Docker](https://docs.docker.com/get-docker/) and 
[Docker Compose](https://docs.docker.com/compose/install/) (version 2.21.0 or higher).

## Installation
First, obtain the latest release of the repository:

=== "CLI (git)"
    ```commandline
    git clone https://github.com/aiondemand/AIOD-rest-api.git
    ```

=== "UI (browser)"
    
    * Navigate to the project page [aiondemand/AIOD-rest-api](https://github.com/aiondemand/AIOD-rest-api). 
    * Click the green `<> Code` button and download the `ZIP` file. 
    * Find the downloaded file on disk, and extract the content.

From the root of the project directory (i.e., the directory with the `docker-compose.yaml` file), run:

=== "Shorthand"
    ```commandline
    ./scripts/up.sh
    ```
=== "Docker Compose"
    ```
    docker compose up -d
    ```

This will start a number of services running within one docker network:

 * Database: a [MySQL](https://dev.mysql.com) database that contains the metadata.
 * Keycloak: an authentication service, provides login functionality.
 * Metadata Catalogue REST API: 
 * Elastic Search: indexes metadata catalogue data for faster keyword searches.
 * Logstash: Loads data into Elastic Search.
 * Deletion: Takes care of cleaning up deleted data.
 * nginx: Redirects network traffic within the docker network.
 * es_logstash_setup: Generates scripts for Logstash and creates Elastic Search indices.

These services are described in more detail in their dedicated pages.
After the previous command was executed successfully, you can navigate to [localhost](http://localhost.com)
and see the REST API documentation. This should look similar to the [api.aiod.eu](https://api.aiod.eu) page.

## Configuration
There are two main places to configure the metadata catalogue services: 
environment variables configured in `.env` files, and REST API configuration in a `.toml` file.
The default files are `./.env` and `./src/config.default.toml` shown below.

If you want to use non-default values, we strongly encourage you not to overwrite the contents of these files.
Instead, you can create `./override.env` and `./config.override.toml` files to override those files.
When using the `./scripts/up.sh` script to launch your services, these overrides are automatically taken into account.

=== "`./src/config/default.toml`"
    ```toml
    --8<-- "./src/config.default.toml"
    ```

=== "`./.env`"
    ```.env
    --8<-- ".env"
    ```

## Updating to New Releases
TODO: Publish to docker hub and have the default docker-compose.yaml pull from docker hub instead.