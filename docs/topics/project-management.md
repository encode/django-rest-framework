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

The [maintenance team for Q1 2015](https://github.com/tomchristie/django-rest-framework/issues/2190):

* [@tomchristie](https://github.com/tomchristie/)
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
    
    Please see the [Project management](http://www.django-rest-framework.org/topics/project-management/) section of our documentation for more details.
    
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
    
    To modify this process for future maintenance cycles make a pull request to the [project management](http://www.django-rest-framework.org/topics/project-management/) documentation.

#### Responsibilities of team members

Team members have the following responsibilities.

* Add triage labels and milestones to tickets.
* Close invalid or resolved tickets.
* Merge finalized pull requests.
* Build and deploy the documentation, using `mkdocs gh-deploy`.

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

    Checklist:

    - [ ] Create pull request for [release notes](https://github.com/tomchristie/django-rest-framework/blob/master/docs/topics/release-notes.md) based on the [*.*.* milestone](https://github.com/tomchristie/django-rest-framework/milestones/***).
    - [ ] Ensure the pull request increments the version to `*.*.*` in [`restframework/__init__.py`](https://github.com/tomchristie/django-rest-framework/blob/master/rest_framework/__init__.py).
    - [ ] Confirm with @tomchristie that release is finalized and ready to go.
    - [ ] Ensure that release date is included in pull request.
    - [ ] Merge the release pull request.
    - [ ] Push the package to PyPI with `./setup.py publish`.
    - [ ] Tag the release, with `git tag -a *.*.* -m 'version *.*.*'; git push --tags`.
    - [ ] Deploy the documentation with `mkdocs gh-deploy`.
    - [ ] Make a release announcement on the [discussion group](https://groups.google.com/forum/?fromgroups#!forum/django-rest-framework).
    - [ ] Make a release announcement on twitter.
    - [ ] Close the milestone on GitHub.
    
    To modify this process for future releases make a pull request to the [project management](http://www.django-rest-framework.org/topics/project-management/) documentation.

When pushing the release to PyPI ensure that your environment has been installed from our development `requirement.txt`, so that documentation and PyPI installs are consistently being built against a pinned set of packages.

---

## Project ownership

The PyPI package is owned by `@tomchristie`. As a backup `@j4mie` also has ownership of the package.

If `@tomchristie` ceases to participate in the project then `@j4mie` has responsibility for handing over ownership duties.

#### Outstanding management & ownership issues

The following issues still need to be addressed:

* [Consider moving the repo into a proper GitHub organization][github-org].
* Ensure `@jamie` has back-up access to the `django-rest-framework.org` domain setup and admin.
* Document ownership of the [live example][sandbox] API.
* Document ownership of the [mailing list][mailing-list] and IRC channel.
* Document ownership and management of the security mailing list.

[bus-factor]: http://en.wikipedia.org/wiki/Bus_factor
[un-triaged]: https://github.com/tomchristie/django-rest-framework/issues?q=is%3Aopen+no%3Alabel
[github-org]: https://github.com/tomchristie/django-rest-framework/issues/2162
[sandbox]: http://restframework.herokuapp.com/
[mailing-list]: https://groups.google.com/forum/#!forum/django-rest-framework
