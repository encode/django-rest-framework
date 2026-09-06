"""
Warning classes used to flag features that are scheduled for removal.

Each `RemovedInDRF3XXWarning` class is named after the release that removes
the feature it flags, so `RemovedInDRF320Warning` marks an API that will stop
working in DRF 3.20.

New deprecations target the release after next, and therefore start out as a
`PendingDeprecationWarning`, which is silent by default. One release later,
they are escalated to a `DeprecationWarning`, before being removed in the
following release. See the deprecation policy for the full timeline:
https://www.django-rest-framework.org/community/release-notes/#deprecation-policy
"""


class RemovedInDRF319Warning(DeprecationWarning):
    pass


class RemovedInDRF320Warning(PendingDeprecationWarning):
    pass


# Aliases that always track the current release cycle, so that projects can
# filter on them without editing their configuration on every DRF release.
RemovedInNextDRFVersionWarning = RemovedInDRF319Warning
RemovedAfterNextDRFVersionWarning = RemovedInDRF320Warning
