# Project management

> "No one can whistle a symphony; it takes a whole orchestra to play it"
>
> &mdash; Halford E. Luccock

This document outlines our project management processes for REST framework.

The aim is to ensure that the project has a high
["bus factor"][bus-factor], and can continue to remain well supported for the foreseeable future. Suggestions for improvements to our process are welcome.

---

## Maintenance team

[Participating actively in the REST framework project](contributing.md) **does not require being part of the maintenance team**. Almost every important part of issue triage and project improvement can be actively worked on regardless of your collaborator status on the repository.

#### Composition

The composition of the maintenance team is handled by [@tomchristie](https://github.com/encode/). Team members will be added as collaborators to the repository.

#### Responsibilities

Team members have the following responsibilities.

* Close invalid or resolved tickets.
* Add triage labels and milestones to tickets.
* Merge finalized pull requests.
* Build and deploy the documentation, using `mkdocs gh-deploy`.
* Build and update the included translation packs.

Further notes for maintainers:

* Code changes should come in the form of a pull request - do not push directly to main.
* Maintainers should typically not merge their own pull requests.
* Each issue/pull request should have exactly one label once triaged.
* Search for un-triaged issues with [is:open no:label][un-triaged].

---

## Release process

* The release manager is selected.
* The release manager will then have the maintainer role added to PyPI package.
* The previous manager will then have the maintainer role removed from the PyPI package.

Our PyPI releases is automated in GitHub actions on tag pushes. The following template can be used as a release checklist:

- Create pull request for [release notes](https://github.com/encode/django-rest-framework/blob/mains/docs/topics/release-notes.md):
    - Start drafting a [new release in GitHub](https://github.com/encode/django-rest-framework/releases/new)
    - Select the tag that you want to give to the release and the previous tag
    - Click the "Generate release notes" button
    - Don't confirm anything! Copy the generated content to a file `input.md`
    - Run `uv tool run linkify-gh-markdown input.md` to make the links absolute
    - Put the generated content in the `release-notes.md` file
- Update supported versions:
    - `pyproject.toml` ensure the `requires-python` key is up to date
    - `pyproject.toml` Python & Django version trove classifiers
    - `README` Python & Django versions
    - `docs` Python & Django versions
- Ensure the pull request increments the version to `*.*.*` in [`restframework/__init__.py`](https://github.com/encode/django-rest-framework/blob/main/rest_framework/__init__.py).
- Ensure documentation validates
    - Build and serve docs `mkdocs serve`
    - Validate links `pylinkvalidate.py -P http://127.0.0.1:8000`
- Confirm with other maintainers that the release is finalized and ready to go.
- Ensure that release date is included in pull request.
- Merge the release pull request.
- Tag the release, either with `git tag -a *.*.* -m 'version *.*.*'; git push --tags` or in GitHub.
- Wait for the release workflow to run. It will build the distribution, upload it to Test PyPI, PyPI and create the GitHub release.
- Make a release announcement on the [discussion group](https://groups.google.com/forum/?fromgroups#!forum/django-rest-framework).
- Make a release announcement on social media (Mastodon, etc...) and on the [Django forum](https://forum.djangoproject.com/).
- Close the milestone on GitHub.

---

## Project ownership

The PyPI package is owned by `@tomchristie`. As a backup `@j4mie` also has ownership of the package.

If `@tomchristie` ceases to participate in the project then `@j4mie` has responsibility for handing over ownership duties.

#### Outstanding management & ownership issues

The following issues still need to be addressed:

* Ensure `@j4mie` has back-up access to the `django-rest-framework.org` domain setup and admin.
* Document ownership of the [mailing list][mailing-list] and IRC channel.
* Document ownership and management of the security mailing list.

[bus-factor]: https://en.wikipedia.org/wiki/Bus_factor
[un-triaged]: https://github.com/encode/django-rest-framework/issues?q=is%3Aopen+no%3Alabel
[mailing-list]: https://groups.google.com/forum/#!forum/django-rest-framework
