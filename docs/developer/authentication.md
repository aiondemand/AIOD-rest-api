# Authentication

For authentication, we use a [keycloak](https://www.keycloak.org) service.
For development, make sure to use the `USE_LOCAL_DEV=true` environment variable so that the local
keycloak server is configured with default users:

| User | Password | Role(s)                                               | Comment |
|------|----------|-------------------------------------------------------|---------|
| user | password | default-roles-aiod, offline_access, uma_authorization |         |

For a description of the roles, see ["AIoD Keycloak Roles"](../hosting/authentication.md#roles).
With the local development configuration, you will only be able to authenticate with keycloak users (OAuth2, password) not by other means.
You can test authentication by e.g.,:

1. Navigate to the Swagger documentation (https://localhost:8000/docs)
2. Click `Authorize`
3. Navigate to "OpenIdConnect (OAuth2, password)" and provide the username and password.
4. Click `Authorize`
5. You should now be logged in. You can verify this by accessing an endpoint that requires authentication, such as `/authorization_test`.

## Connecting to Keycloak Console
To connect to the Keycloak console, visit http://localhost/aiod-auth.
In the development instance the administrator username is 'admin' and its password 'password'.
