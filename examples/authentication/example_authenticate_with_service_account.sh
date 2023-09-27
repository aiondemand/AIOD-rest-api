#!/bin/bash
# This minimal example is for back-end services that want to authenticate as a server.
# Use this example if you want to upload data in the name of the service, not in the name
# of a user.
# Another option for back-end services would be to let users login / to impersonate users.



# Ask admin of https://aiod-dev.i3a.es/aiod-auth keycloak, e.g. Rafael, for a secret
CLIENT_ID="PUT CLIENT ID HERE"
SECRET="PUT THE SECRET HERE"


if [ "${CLIENT_ID}" = "PUT CLIENT ID HERE" ]; then
  echo "Error: put the correct client id in the script"
  exit 1
fi
if [ "${SECRET}" = "PUT THE SECRET HERE" ]; then
  echo "Error: put the correct secret in the script"
  exit 1
fi


TOKEN_DICT=$(curl \
  -d "client_id=${CLIENT_ID}" \
  -d "client_secret=${SECRET}" \
  -d "grant_type=client_credentials" \
  -d "scope=openid profile roles" \
  "https://aiod-dev.i3a.es/aiod-auth/realms/aiod/protocol/openid-connect/token" \
  | python3 -m json.tool
)

TOKEN=$(
  echo $TOKEN_DICT \
    | jq .access_token \
    | tr -d '"'
)

echo "TOKEN: "
echo $TOKEN
echo "(should not be null)"

RESULT=$(
  curl -X 'GET' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    https://aiod-dev.i3a.es/authorization_test
)


echo "Result of auth test:"
echo $RESULT
