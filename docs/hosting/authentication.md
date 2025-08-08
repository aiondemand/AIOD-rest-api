# Keycloak Service

When running the metadata catalogue in production, you want to ensure that users can authenticate
so that proper authorization over the endpoints can take place.
Keycloak is typically configured to allow users to sign on with credentials from other services,
such as a Google account or an institutional one.

## Configuring Keycloak
To configure Keycloak, set the following environment variables (preferably through the `override.env` file):

 * `HOSTNAME`: URL for issued tokens ([documentation](https://www.keycloak.org/server/hostname)). For example: `auth.aiod.eu`.
 * `AIOD_KEYCLOAK_PORT`: The port at which the Keycloak server should be available in the host machine, e.g., `8081`.
 * `REDIRECT_URIS`: URI a successful login action should redirect back to. E.g., `https://${HOSTNAME}/docs/oauth2-redirect`.
 * `POST_LOGOUT_REDIRECT_URIS`: URI a successful logout action should redirect back to. E.g., `https://${HOSTNAME}/aiod-auth/realms/aiod/protocol/openid-connect/logout`.

As well as the `openid_connect_url` in `./src/config.override.toml` (for authentication on the Swagger page):
```toml
[keycloak]
openid_connect_url = "https://auth.aiod.eu/aiod-auth/realms/aiod/.well-known/openid-configuration"
```

## Using External Identity Providers

There are two ways to integrate external identity providers (e.g. Google, [EGI Check-in](https://docs.egi.eu/users/aai/check-in/)).

Create both a private and a public client in the external provider (this step is required for both options below).

### Option 1: Update the configuration files
   - Replace `KEYCLOAK_CLIENT_SECRET` in `override.env` with the value provided by the external IdP.
   - Update `server_url`, `client_id`, `client_id_swagger` `openid_connect_url` and `scopes` in `./src/config.override.toml`.
   - In this setup, the Keycloak container is not required and can be shut down.
### Option 2: use keycloak as an identity broker
   - Details can be found in the Keycloak documentation: [Integrating identity providers](https://www.keycloak.org/docs/latest/server_admin/index.html#_identity_broker).
   - This method allows to configure multiple IdPs.

[//]: # (Should include information on how to run it locally then...)

## Roles

Roles identify a type or category of user and determine their access and permissions within applications.
Roles are generally only necessary for special cases.
The normal flow for granting individual users permissions for individual assets is detailed in the ["user model"](../developer/users.md) documentation.
These are the roles the metadata catalogue uses (`*` in a role indicates its defined for each asset type individually):

 * `review_aiod_resources`: identifies the user as having permission to view asset submissions and review them.
 * `read_*`: allows the user read access to all assets on the platform, regardless of the asset-specific permissions.
 * `update_*`: allows the user update permission for all assets on the platform, regardless of the asset-specific permissions.
 * `delete_*`: allows the user delete permission for all assets on the platform, regardless of the asset-specific permissions.
 * `create_platforms`: allows the user to define new platforms.
 * `platform_NAME`: identifies the 'user' as being allowed to register assets of platform 'NAME', used for connectors.

Note that roles may be used for services other than the metadata catalogue.
New roles can be created from the admin console, see ["Creating a realm role"](https://www.keycloak.org/docs/latest/server_admin/index.html#proc-creating-realm-roles_server_administration_guide).

[//]: # ( Are we missing roles? Check admin console. Are all roles still relevant? delete if not)

## Verifying Keycloak is Working

To verify the Keycloak service is configured correctly using the Swagger interface, follows these steps:

 1. Open your browser and go to `http://$HOSTNAME`
 2. Go to `/authorization_test`, click on `try it out` and `execute`.
    - You should get an `Error: Unauthorized`
 3. Log in:
    - Click the `Authorize` button in the top-right corner.
    - Select `OpenIdConnect (OAuth2, authorization_code with PKCE)`.
    - Click `Authorize` and log in using any available identity provider.
 4. Return to `/authorization_test`, click `try it out` and then `execute` again.

If authentication is successful, the request should now be authtorised.

## Importing and Exporting Realm and User Files
See also ["Importing and Exporting Realms"](https://www.keycloak.org/server/importExport) in the Keycloak documentation.

Keycloak has "realm" configurations (e.g., roles that exist for AIoD),
as well as "user" configurations (e.g., user Alice with password X is a Reviewer).
We advise to export these separately, so you can share the non-sensitive realm configuration
without sharing sensitive user information.

To **export** run the following command while the keycloak container is running:
```bash
docker exec -it keycloak /opt/keycloak/bin/kc.sh export --dir /opt/keycloak/data/export  --realm aiod
```

This puts the exported files in the `${DATA_PATH}/keycloak/data/export` directory.

To **import**, just place the export files into the `{DATA_PATH}/keycloak/data/import` directory.
When running the `develop` preset using `USE_LOCAL_DEV=true`, the import directly is populated by the data found in `./authentication/import/`.
