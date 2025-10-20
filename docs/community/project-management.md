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

* The release manager is selected by `@tomchristie`.
* The release manager will then have the maintainer role added to PyPI package.
* The previous manager will then have the maintainer role removed from the PyPI package.

Our PyPI releases will be handled by either the current release manager, or by `@tomchristie`. Every release should have an open issue tagged with the `Release` label and marked against the appropriate milestone.

The following template should be used for the description of the issue, and serves as a release checklist.

    Release manager is @***.
    Pull request is #***.

    Checklist:

    - [ ] Create pull request for [release notes](https://github.com/encode/django-rest-framework/blob/mains/docs/topics/release-notes.md) based on the [*.*.* milestone](https://github.com/encode/django-rest-framework/milestones/***).
    - [ ] Update supported versions:
        - [ ] `pyproject.toml` `python_requires` list
        - [ ] `pyproject.toml` Python & Django version trove classifiers
        - [ ] `README` Python & Django versions
        - [ ] `docs` Python & Django versions

    - [ ] Ensure the pull request increments the version to `*.*.*` in [`restframework/__init__.py`](https://github.com/encode/django-rest-framework/blob/main/rest_framework/__init__.py).
    - [ ] Ensure documentation validates
        - Build and serve docs `mkdocs serve`
        - Validate links `pylinkvalidate.py -P http://127.0.0.1:8000`
    - [ ] Confirm with @tomchristie that release is finalized and ready to go.
    - [ ] Ensure that release date is included in pull request.
    - [ ] Merge the release pull request.
    - [ ] Install the release tools: `pip install build twine`
    - [ ] Build the package: `python -m build`
    - [ ] Push the package to PyPI with `twine upload dist/*`
    - [ ] Tag the release, with `git tag -a *.*.* -m 'version *.*.*'; git push --tags`.
    - [ ] Deploy the documentation with `mkdocs gh-deploy`.
    - [ ] Make a release announcement on the [discussion group](https://groups.google.com/forum/?fromgroups#!forum/django-rest-framework).
    - [ ] Make a release announcement on twitter.
    - [ ] Close the milestone on GitHub.

    To modify this process for future releases make a pull request to the [project management](https://www.django-rest-framework.org/topics/project-management/) documentation.

When pushing the release to PyPI ensure that your environment has been installed from our development `requirement.txt`, so that documentation and PyPI installs are consistently being built against a pinned set of packages.

---

## Project requirements

All our test requirements are pinned to exact versions, in order to ensure that our test runs are reproducible. We maintain the requirements in the `requirements` directory. The requirements files are referenced from the `tox.ini` configuration file, ensuring we have a single source of truth for package versions used in testing.

Package upgrades should generally be treated as isolated pull requests. You can check if there are any packages available at a newer version, by using the `pip list --outdated`.

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
