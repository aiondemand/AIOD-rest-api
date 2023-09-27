#!/bin/bash
# This minimal example uses service authentication.



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


echo "POSTING a new dataset..."

# Only a name is added for this dataset. See https://aiod-dev.i3a.es/docs#/ for all possible fields.
RESULT=$(
  curl -X 'POST' \
    -H "Accept: application/json" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{"name": "test"}' \
    https://aiod-dev.i3a.es/datasets/v1
)



IDENTIFIER=$(
  echo $RESULT \
    | jq .identifier \
    | tr -d '"'
)
echo "Identifier of the new dataset (should not be null):"
echo $IDENTIFIER


echo "Trying to retrieve the just posted dataset of the platform..."
NEW_DATASET=$(
  curl -X 'GET' \
    -H "Accept: application/json" \
    https://aiod-dev.i3a.es/datasets/v1/${IDENTIFIER}
)
echo "New dataset as found on the platform:"
echo $NEW_DATASET | jq .


echo "Deleting the dataset again, because it was just a test..."
DELETED=$(
  curl -X 'DELETE' \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Accept: application/json" \
    https://aiod-dev.i3a.es/datasets/v1/${IDENTIFIER}
)
echo "Done."
