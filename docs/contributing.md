# Contributing

You're looking to contribute to the AI-on-Demand metadata catalogue, that's great!
AI-on-Demand is an open project and we welcome contributions by all, no matter their experience or background.

## Types of Contributions
There are many types of contributions to be made to the metadata catalogue, and this section
covers a non-exhaustive list. If you find something that's not outlined here, just reach out to us!

### No Code
Good examples for contributions that do not require any coding include:

 - Giving [our GitHub repository](https://github.com/aiondemand/AIOD-rest-api) a star ⭐️
 - [Helping people on the GitHub issue tracker](#helping-people-on-github) 🤝
 - [Reporting bugs](#reporting-bugs) 🐛

### Documentation
You can help improve our documentation by correcting mistakes, such as typos, adding clarifications,
or even adding new sections. For small changes, documentation can be edited directly on GitHub by
finding the related markdown file and clicking the pencil icon in the top-right corner (✐).

If you intend to make bigger changes, please first open a new issue the documents the suggested change.
That way, we can give you feedback before you write, and verify that it is actually a change we would be interested in adopting.
For big changes, we also recommend you to follow the instructions on ["Setting up a development environment"](#setting-up-a-development-environment)
so that you can render the changed documentation locally.

### Code
For code changes, please first coordinate with the developers on what you will work on.
You can do this by either leaving a comment on an existing issue that you would like to help with,
or by opening a new issue proposing your change. By first communicating with the developers, they
can let you know ahead of time whether or not the change is wanted, make sure they have time to
support you, and provide any feedback. We really want to avoid a scenario where you may work hard on a contribution
only to find out that it is not in line with the vision of the project and thus will not be accepted.
When starting your first code contribution, visit the ["Setting up a development environment"](#setting-up-a-development-environment)
section for more information on how to get started.

## Helping people on GitHub
Helping people on the [GitHub issue tracker](https://github.com/aiondemand/AIOD-rest-api/issues) just requires a GitHub account.
You can help by people by answering their questions, or weighing in on discussions.
Even if you do not have an answer, you can verify that you can reproduce the behavior they report or
ask clarifying questions to make their bug report better (see also ["Reporting Bugs"](#reporting-bugs)).
This helps the core contributors resolve the issue with more ease and is hugely appreciated.
As always, please be kind and patient with others.

## Reporting Bugs
When you find a bug and want to report it, the first step is to check that it has not already been reported.
Use the search functionality of the GitHub issue tracker to find identical or related issues.
If your issue or bug has already been reported, please do not open a new issue.
Instead, either "upvote" the original report by leaving a 👍 reaction or,
if you have additional information which may be relevant to the discussion, leave a comment on that issue.

If your bug isn't reported yet, create a new issue.
Provide a clear explanation of the expected behavior and the observed behavior, and explain why you think this is a bug.
Add instructions on how to reproduce the expected behavior through a [Minimal Reproducible Example](https://stackoverflow.com/help/minimal-reproducible-example).
Without it, it may be very hard for contributors to solve the issue (or may not even understand it).

## Setting up a development environment

### Cloning
First, make sure you can get the local metadata catalogue up and running by following the ["Hosting" instructions](hosting/index.md).
During the installation step, use `git` to clone the repository.
If you have write access to this repository, you can follow the instruction as-is.
If you do not have write access to this repository, you must [fork it](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/fork-a-repo).
After forking the repository, your clone command will be (substituting `USERNAME` for your GitHub username):

```commandline
git clone https://github.com/USERNAME/AIOD-rest-api.git
```

### Installing Dependencies
Always make sure to install your dependencies in a local environment, for example with the built in `venv` module:

```commandline
python -m venv venv
source venv/bin/activate
```

and then install the Python dependencies

```commandline
python -m pip install -e ".[dev, docs]"
```

we install the optional `dev` (developer) and `docs` (documentation) dependencies so that we can
build documentation and run tests locally.

### Configuration

It is also generally useful to set add an `override.env` file to the project's root directory with
the line `USE_LOCAL_DEV=true` added. This will allow utility scripts `./scripts/up.sh` and `./scripts/down.sh`
to start docker containers in a way that reflects local changes.

### Pre-commit
Finally, configure your [pre-commit](https://pre-commit.com) hooks using `pre-commit install`.
This will install some hooks to run before a commit can be made, these hooks will run various checks such as a code formatter, linter, file validation, and unit tests.
These hooks help make sure formatting is more homogeneous across the project, and that no breaking changes are accidentally committed.

## Making a Code Changes
See the ["Developer Documentation"](developer/index.md) for the technical documentation of this project.
More to be added.

Note that when using our convenience scripts to launch docker containers (see ["Shorthands"](hosting/index.md#shorthands)),
local code changes are not mounted to the docker containers unless `USE_LOCAL_DEV` is set to `true`. You should configure this
variable in your `override.env`.

[//]: # (## Setting up a pull request)
