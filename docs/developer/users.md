# User Model

The user model in AIoD allows users to maintain and share ownership over assets,
and to allow a review process for new assets.
The components of this user model are defined in [src/database/authorization.py](https://github.com/aiondemand/AIOD-rest-api/blob/develop/src/database/authorization.py)
and [src/database/review.py](https://github.com/aiondemand/AIOD-rest-api/blob/develop/src/database/review.py).
Note that for special users (e.g., administrators), this user model may be circumvented through
special Keycloak roles (for more information, see ["Roles"](../hosting/authentication.md)).

[//]: # (Add a diagram overview once the model is more final, e.g., groups are added)

## Users
User credentials are kept in keycloak or by identity providers, in any case the user is uniquely identified
by the unique "sub" key that keycloak provides in its token.
In our user model we keep as little information about the user as we can.
This avoids a scenario were data is kept twice and may desynchronize, and also respects the users' privacy.
Currently, that is only the "sub", but in the future we may consider adding e.g., usernames.

## Permissions
A user may have certain permissions for an asset, these are:

 - read: a user may retrieve this metadata asset.
 - write: a user may modify this metadata asset.
 - admin: a user may delete this metadata asset, submit it for review, and grant other users permissions for the asset.

The only notion of "ownership" over a particular metadata asset is having administrator rights.
When user A uploads an asset and assigns user B administrator rights, they have completely equal rights.
There is no special privilege for user A, and this also means that e.g., user B may remove administrator rights from user A.

## Reviews

!!! info
    The upload and review process is described from a user perspective in ["Uploading"](../using/upload.md).

An asset uploaded by a user is by default in `draft` state.
The user may request the asset to be `published` by submitting it for review through the REST API.
To do this, they submit the identifier of the asset to the `ASSET_TYPE/submit/v1/{identifier}` endpoint.
When it is submitted for review, reviewers will be able to see the request and make a decision.
As long as no decision has been made, the user may retract their submission from review using the `ASSET_TYPE/retract/v1/{identifier}`
endpoint.
Each asset may only have one concurrent review request, and the asset may not be modified while it is under review.

Reviewers can find pending submissions using the `submissions/v1` endpoint,
and get information on a particular submission with the `submissions/v1/{identifier}` endpoint,
where the identifier denotes the identifier of the submission (i.e., review request).
Reviewers can submit a review using the `ASSET_TYPE/review/v1/{identifier}` endpoint.

If the submission is accepted, the asset will be published without further action from the original uploader.
If the submission is rejected, the asset will move back to `draft` state and may be submitted again.
