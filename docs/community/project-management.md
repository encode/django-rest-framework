# Project management

> "No one can whistle a symphony; it takes a whole orchestra to play it"
>
> &mdash; Halford E. Luccock

This document outlines our project management processes for REST framework.

The aim is to ensure that the project has a high
["bus factor"][bus-factor], and can continue to remain well supported for the foreseeable future. Suggestions for improvements to our process are welcome.

---

## Maintenance team

We have a quarterly maintenance cycle where new members may join the maintenance team. We currently cap the size of the team at 5 members, and may encourage folks to step out of the team for a cycle to allow new members to participate.

#### Current team

The [maintenance team for Q4 2015](https://github.com/encode/django-rest-framework/issues/2190):

* [@tomchristie](https://github.com/encode/)
* [@xordoquy](https://github.com/xordoquy/) (Release manager.)
* [@carltongibson](https://github.com/carltongibson/)
* [@kevin-brown](https://github.com/kevin-brown/)
* [@jpadilla](https://github.com/jpadilla/)

#### Maintenance cycles

Each maintenance cycle is initiated by an issue being opened with the `Process` label.

* To be considered for a maintainer role simply comment against the issue.
* Existing members must explicitly opt-in to the next cycle by check-marking their name.
* The final decision on the incoming team will be made by `@tomchristie`.

Members of the maintenance team will be added as collaborators to the repository.

The following template should be used for the description of the issue, and serves as the formal process for selecting the team.

    This issue is for determining the maintenance team for the *** period.

    Please see the [Project management](https://www.django-rest-framework.org/topics/project-management/) section of our documentation for more details.

    ---

    #### Renewing existing members.

    The following people are the current maintenance team. Please checkmark your name if you wish to continue to have write permission on the repository for the *** period.

    - [ ] @***
    - [ ] @***
    - [ ] @***
    - [ ] @***
    - [ ] @***

    ---

    #### New members.

    If you wish to be considered for this or a future date, please comment against this or subsequent issues.

    To modify this process for future maintenance cycles make a pull request to the [project management](https://www.django-rest-framework.org/topics/project-management/) documentation.

#### Responsibilities of team members

Team members have the following responsibilities.

* Close invalid or resolved tickets.
* Add triage labels and milestones to tickets.
* Merge finalized pull requests.
* Build and deploy the documentation, using `mkdocs gh-deploy`.
* Build and update the included translation packs.

Further notes for maintainers:

* Code changes should come in the form of a pull request - do not push directly to master.
* Maintainers should typically not merge their own pull requests.
* Each issue/pull request should have exactly one label once triaged.
* Search for un-triaged issues with [is:open no:label][un-triaged].

It should be noted that participating actively in the REST framework project clearly **does not require being part of the maintenance team**. Almost every import part of issue triage and project improvement can be actively worked on regardless of your collaborator status on the repository.

---

## Release process

The release manager is selected on every quarterly maintenance cycle.

* The manager should be selected by `@tomchristie`.
* The manager will then have the maintainer role added to PyPI package.
* The previous manager will then have the maintainer role removed from the PyPI package.

Our PyPI releases will be handled by either the current release manager, or by `@tomchristie`. Every release should have an open issue tagged with the `Release` label and marked against the appropriate milestone.

The following template should be used for the description of the issue, and serves as a release checklist.

    Release manager is @***.
    Pull request is #***.

    During development cycle:

    - [ ] Upload the new content to be translated to [transifex](https://www.django-rest-framework.org/topics/project-management/#translations).


    Checklist:

    - [ ] Create pull request for [release notes](https://github.com/encode/django-rest-framework/blob/master/docs/topics/release-notes.md) based on the [*.*.* milestone](https://github.com/encode/django-rest-framework/milestones/***).
    - [ ] Update supported versions:
        - [ ] `setup.py` `python_requires` list
        - [ ] `setup.py` Python & Django version trove classifiers
        - [ ] `README` Python & Django versions
        - [ ] `docs` Python & Django versions
    - [ ] Update the translations from [transifex](https://www.django-rest-framework.org/topics/project-management/#translations).
    - [ ] Ensure the pull request increments the version to `*.*.*` in [`restframework/__init__.py`](https://github.com/encode/django-rest-framework/blob/master/rest_framework/__init__.py).
    - [ ] Confirm with @tomchristie that release is finalized and ready to go.
    - [ ] Ensure that release date is included in pull request.
    - [ ] Merge the release pull request.
    - [ ] Push the package to PyPI with `./setup.py publish`.
    - [ ] Tag the release, with `git tag -a *.*.* -m 'version *.*.*'; git push --tags`.
    - [ ] Deploy the documentation with `mkdocs gh-deploy`.
    - [ ] Make a release announcement on the [discussion group](https://groups.google.com/forum/?fromgroups#!forum/django-rest-framework).
    - [ ] Make a release announcement on twitter.
    - [ ] Close the milestone on GitHub.

    To modify this process for future releases make a pull request to the [project management](https://www.django-rest-framework.org/topics/project-management/) documentation.

When pushing the release to PyPI ensure that your environment has been installed from our development `requirement.txt`, so that documentation and PyPI installs are consistently being built against a pinned set of packages.

---

## Translations

The maintenance team are responsible for managing the translation packs include in REST framework. Translating the source strings into multiple languages is managed through the [transifex service][transifex-project].

### Managing Transifex

The [official Transifex client][transifex-client] is used to upload and download translations to Transifex. The client is installed using pip:

    pip install transifex-client

To use it you'll need a login to Transifex which has a password, and you'll need to have administrative access to the Transifex project. You'll need to create a `~/.transifexrc` file which contains your credentials.

    [https://www.transifex.com]
    username = ***
    token = ***
    password = ***
    hostname = https://www.transifex.com

### Upload new source files

When any user visible strings are changed, they should be uploaded to Transifex so that the translators can start to translate them. To do this, just run:

    # 1. Update the source django.po file, which is the US English version.
    cd rest_framework
    django-admin makemessages -l en_US
    # 2. Push the source django.po file to Transifex.
    cd ..
    tx push -s

When pushing source files, Transifex will update the source strings of a resource to match those from the new source file.

Here's how differences between the old and new source files will be handled:

* New strings will be added.
* Modified strings will be added as well.
* Strings which do not exist in the new source file will be removed from the database, along with their translations. If that source strings gets re-added later then [Transifex Translation Memory][translation-memory] will automatically include the translation string.

### Download translations

When a translator has finished translating their work needs to be downloaded from Transifex into the REST framework repository. To do this, run:

    # 3. Pull the translated django.po files from Transifex.
    tx pull -a --minimum-perc 10
    cd rest_framework
    # 4. Compile the binary .mo files for all supported languages.
    django-admin compilemessages

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

* Ensure `@jamie` has back-up access to the `django-rest-framework.org` domain setup and admin.
* Document ownership of the [live example][sandbox] API.
* Document ownership of the [mailing list][mailing-list] and IRC channel.
* Document ownership and management of the security mailing list.

[bus-factor]: https://en.wikipedia.org/wiki/Bus_factor
[un-triaged]: https://github.com/encode/django-rest-framework/issues?q=is%3Aopen+no%3Alabel
[transifex-project]: https://www.transifex.com/projects/p/django-rest-framework/
[transifex-client]: https://pypi.org/project/transifex-client/
[translation-memory]: http://docs.transifex.com/guides/tm#let-tm-automatically-populate-translations
[sandbox]: https://restframework.herokuapp.com/
[mailing-list]: https://groups.google.com/forum/#!forum/django-rest-framework
