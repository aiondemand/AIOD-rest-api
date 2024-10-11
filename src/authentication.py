"""
We use keycloak for authentication and authorization.

The overall idea is that:
- The frontend uses a public client (without a secret) and authenticates the user
- The frontend passes the token to the backend
- The backend (i.e. this project) decodes the token to obtain the username
- The backend performs an authorization request to Keycloak, obtaining the permissions. It uses a
    private client for this request.

The main reason to perform a separate authorization request in the backend is that the frontend
should not be responsible for keeping the permissions up to date. Explanation: instead of only
obtaining the permissions from the decoded token, the backend could also take the permissions.
This is perfectly safe (the token cannot be changed without knowing the private key of keycloak).
But then the frontend needs to make sure that the permissions are up-to-date. Every front-end
should therefore request a new token every X minutes. This is not needed when the back-end
performs a separate authorization request. The only downside is the overhead of the additional
keycloak requests - if that becomes prohibitive in the future, we should reevaluate this design.
"""

import logging
import os

from dotenv import load_dotenv
from fastapi import HTTPException, Security, status
from fastapi.security import OpenIdConnect
from keycloak import KeycloakOpenID
from pydantic import BaseModel, Field

from config import KEYCLOAK_CONFIG

load_dotenv()


oidc = OpenIdConnect(openIdConnectUrl=KEYCLOAK_CONFIG.get("openid_connect_url"), auto_error=False)


client_secret = os.getenv("KEYCLOAK_CLIENT_SECRET")
keycloak_openid = KeycloakOpenID(
    server_url=KEYCLOAK_CONFIG.get("server_url"),
    client_id=KEYCLOAK_CONFIG.get("client_id"),
    client_secret_key=client_secret,
    realm_name=KEYCLOAK_CONFIG.get("realm"),
    verify=True,
)


class User(BaseModel):
    name: str = Field(description="The username.")
    roles: set[str] = Field(description="The roles.")
    subject_identifier: str = Field(
        description="Unique identifier for the user that created the resource."
    )

    def has_role(self, role: str) -> bool:
        return role in self.roles

    def has_any_role(self, *roles: str) -> bool:
        return bool(set(roles) & self.roles)


async def _get_user(token) -> User:
    """
    Check the roles of the user for authorization.

    Raises:
        NoTokenError on missing token (unauthorized message) and InvalidUserError on inactive user.
        Also HTTPException with status 401 on any problem with the token
        (we don't want to leak information), and status 500 on any request
        if Keycloak is configured incorrectly.
    """
    if not client_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="This instance is not configured correctly. You'll need to set the env var "
            "KEYCLOAK_CLIENT_SECRET (e.g. in src/.env). You need to obtain this secret "
            "from a Keycloak Administrator of AIoD.",
        )
    if not token:
        raise NoTokenError("No token found")
    try:
        token = token.replace("Bearer ", "")
        # query the authorization server to determine the active state of this token and to
        # determine meta-information.
        userinfo = keycloak_openid.introspect(token)

        if not userinfo.get("active", False):
            logging.error("Invalid userinfo or inactive user.")
            raise InvalidUserError("Invalid userinfo or inactive user")  # caught below
        return User(
            name=userinfo["username"],
            roles=set(userinfo.get("realm_access", {}).get("roles", [])),
            subject_identifier=userinfo["sub"],
        )
    except InvalidUserError:
        raise
    except Exception as e:
        logging.error(f"Error while checking the access token: '{e}'")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_user_or_none(token=Security(oidc)) -> User | None:
    """
    Use this function in Depends() to ask for authentication.
    This method should be only used to get the current user
    without raising exception when the token is not found,
    or the user is not active, or the userinfo is invalid.
    """
    try:
        return await _get_user(token)
    except (NoTokenError, InvalidUserError):
        return None


async def get_user_or_raise(token=Security(oidc)) -> User:
    """
    Use this function in Depends() to force authentication. Check the roles of the user for
    authorization.

    Raises:
        HTTPException with status 401 on missing token (unauthorized message), or invalid user.
        It also raises a HTTPException with status 401 on
        any problem with the token (we don't want to leak information),
        status 500 on any request if Keycloak is configured incorrectly.
    """
    try:
        return await _get_user(token)
    except (InvalidUserError, NoTokenError) as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"{err} - This endpoint requires authorization. You need to be logged in.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from err


class InvalidUserError(Exception):
    """Raise an error on invalid userinfo or inactive user."""


class NoTokenError(Exception):
    """Raise an error when no token is found."""
