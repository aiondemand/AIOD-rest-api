# Uploading to the Metadata Catalogue

There are two ways for metadata to be registered into the metadata catalogue.
The first is an automated process where connector services automatically index
information from popular AI and research platforms such as [Hugging Face](https://huggingface.co).
The second is to directly register metadata with the metadata catalogue.
This may be done directly through the REST API, or by services built on top of it
such as [RAIL](https://rail.aiod.eu) or the (to be added) metadata catalogue editor.

This page describes the steps to register metadata through the REST API.

## What is *meta*data?
*Meta*data is data about data. A tabular dataset stored in an excel sheet or a trained
machine learning model is the *data*. The *meta*data then describes information
about that data, for example, "how big is the dataset?", "how was the model trained?",
"where is the data stored?" or "which publication describes the data?".

The metadata catalogue does not provide an option to upload the data alongside the
metadata. If you want to upload your model or dataset, we recommend you do this in
platforms that specialize in storing this artifacts, such as [Zenodo](https://zenodo.org),
[OpenML](https://openml.org), or [Hugging Face](https://huggingface.co).
If you do this with a platform which has a [connector](../hosting/connectors.md) to
the metadata catalogue, the metadata for that asset will automatically be registered
in the metadata catalogue and there is no need to manually register it as described
below.

In the future there may also be services on the AI-on-Demand platform which can be
used for data storage.

## Workflow for Uploading Metadata

Registering new metadata requires a user to submit it to the metadata catalogue's REST API,
after which a reviewer will publish the asset or suggest changes. This general workflow
is shown in the image below. In the image and the description after `ASSET` denotes
a type of asset, e.g., `Organisation` or `FundingOpportunity`. Refer to the [REST API
documentation](https://api.aiod.eu/docs) for more information about the latest versions
of the endpoints, including their exact addresses and schemas used.

![Flowchart that depicts the upload process](../media/upload_and_review.svg)

The sections below describe the process in more detail.

### Registering the Asset
You upload your assets to `/ASSET` using a `POST` request that contains
in the JSON body all the required data for the asset type. A successful response
should look something like this:

```json
{
  "identifier": "case_n8DhfFgMYv4beBnVurHa13ZS"
}
```

Take a note of the identifier assigned to the asset, as you will need it to request a review in the next step.
The asset is now in draft mode, which means that other users cannot see it but you can, and you may still edit it.
To edit the asset, use the `PUT` endpoints for `/ASSET`.

### Requesting a Review
When you want to publish the asset, you can submit it for review. You
can do this by making a `POST` request to the `/submissions` endpoint.
You are required to include the identifier in the request body,
and may include a comment to the reviewer of up to 256 characters in the body of the
`POST` request, this should generally not be necessary but may be useful to provide
some clarification. You may supply more than one asset identifier at once,
these assets will then be accepted and rejected together.

```json
{
  "asset_identifiers": ["case_n8DhfFgMYv4beBnVurHa13ZS"],
  "comment": "Clarification the reviewer should be aware of."
}
```

When you request a submission, you get a response with the submission's identifier.

```json
{
  "submission_identifier": 1
}
```
Again, it's useful to save this identifier for later.

!!! info
    An asset submitted for review may longer be edited.
    If you do not want it published, you may [retract the asset](#retracting-a-submission)
    from review after which you are allowed to edit it again.

### Awaiting a Review
After submitting your asset for review, you must wait for a reviewer to process your
submission. If the reviewer accepts the submission, it will be published to AIoD without
further action by you. If the reviewer rejects the submission, you can find their feedback
in their review.

You can check that status of your pending submission in two ways.
First, you can request the status for that review specifically using the
`/submissions/IDENTIFIER` endpoint, where `IDENTIFIER` needs to replaced with the
identifier of the _submission_ (not the asset!).
For example, if the submission identifier we received was '1', we can query
`submissions/1` and retrieve its status which would look something like:
```json
{
  "comment": "Clarification the reviewer should be aware of.",
  "identifier": 1,
  "request_date": "2025-03-20T09:09:54",
  "aiod_entry_identifier": 212,
  "reviews": [],
  "assets": [{
    ...
  }]
}
```
No reviews have yet been performed on the submission, as indicated by the empty list
of reviews (`"reviews": []`).

Alternatively, you can request an overview of all your submissions with a `GET` request
to the `submissions` endpoint, which will result in a response such as:
```json
[
  {
    "comment": "Clarification the reviewer should be aware of.",
    "identifier": 1,
    "request_date": "2025-03-20T09:09:54",
    "aiod_entry_identifier": 212,
    "asset_identifiers": ["case_n8DhfFgMYv4beBnVurHa13ZS"],
  }
]
```
This endpoint fetches and returns minimal information of the submission, which makes it
more lightweight for creating an overview. However, it does not return the status of the
submissions directly. Instead, you may use query parameters to request only a subset of
the submissions, such as those that still require a review (i.e., pending submissions)
by querying `submissions?mode=pending`.
Please refer to the endpoint documentation for other options.

Users are only ever able to view information about their own submissions.
While it is registered in the database which user requested the submission,
this information is not revealed to the reviewer. That is to say, it is a
double-blind review process (though in general the content of the metadata
is likely revealing).

#### Retracting a Submission
Sometimes you may want to retract a submitted asset before a reviewer manages to review it.
For example, to correct a mistake in the original submission. You can retract an asset from
review at any time by doing a `POST` request to the `/submissions/retract/SUBMISSION_IDENTIFIER`
endpoint.

A retracted submission is treated the same as a rejected submission. The asset is put back
into draft status and will not be reviewed until you submit a new review request.

### A Rejected Submission
You may find that your submission gets rejected. In that case, the `submissions/IDENTIFIER`
endpoint will provide you with the reviewer feedback, e.g.:
```json
{
  "comment": "Clarification the reviewer should be aware of.",
  "identifier": 1,
  "request_date": "2025-03-20T09:09:54",
  "aiod_entry_identifier": 212,
  "reviews": [
    {
      "comment": "Several critical fields have incomplete information. Please improve the description, and add a house number to the address.",
      "identifier": 1,
      "decision_date": "2025-03-20T09:23:27",
      "decision": "rejected",
      "submission_identifier": 1
    }
  ],
  "assets": [{ ... }]
}
```
You'll find reviewer comments under "reviews".
You may subsequently edit your asset using `PUT` requests to `/ASSET` to address
the reviewer feedback, and then request a new review following the regular submission
process.


## Reviewer Process
Reviewers are user with a special role assigned in Keycloak.
They have access to all submissions and can review them.
The only restriction is that a reviewer cannot review their own submission.

For reviewers, the main endpoints of interest are:

  * `/submissions` to fetch identifiers of submissions which require a review.
The `?mode=oldest` parameter can be used to fetch the submission which has been waiting for a review the longest.
  * `/submissions/{identifier}` to get more detailed information on the submission,
in particular this will provide also the asset body to review.
  * `/reviews/v1` the endpoint through which reviews can be made using `POST` requests.

Given a submission identifier (obtained from either `/submissions` endpoint mentioned above),
the review can post a review to `/reviews`. This requires the user to make a decision
to accept or reject the submission, and optionally leave a comment. When rejecting an
asset, a comment is strongly encouraged, otherwise the user will not know how to improve
their submission. An example body of the `POST` request to `/reviews` could look like:
```json
{
  "comment": "Several critical fields have incomplete information. Please improve the description, and add a house number to the address.",
  "decision": "rejected",
  "submission_identifier": 0
}
```
The comment may be up to 1800 characters long, so detailed feedback can be given.

## Sharing Access
By default, items are private when they are in draft or under submission.
When items are published, they are publicly readable.
However, you are the only person with the ability to edit or remove them.

You can allow others to see assets which are still private, or give users administrator
or write permissions for individual assets. For more information, see the `/assets/permissions`
endpoints.


## Notes
Assets registered by users will automatically be associated with the "AIoD" platform,
indicating that it's a direct registration. Users cannot associate their registered
metadata with other platforms, as that is reserved to data which is automatically
registered through connectors.

Platforms cannot be created by regular users, and require a special permission set in Keycloak.

There is currently no mechanism for pushing notifications to users, so we cannot notify a user
directly when their assets are published. Some polling mechanism needs to be used for now.
