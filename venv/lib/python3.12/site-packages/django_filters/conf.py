from django.conf import settings as dj_settings
from django.core.signals import setting_changed
from django.utils.translation import gettext_lazy as _

from .utils import deprecate

DEFAULTS = {
    "DISABLE_HELP_TEXT": False,
    "DEFAULT_LOOKUP_EXPR": "exact",
    # empty/null choices
    "EMPTY_CHOICE_LABEL": "---------",
    "NULL_CHOICE_LABEL": None,
    "NULL_CHOICE_VALUE": "null",
    "VERBOSE_LOOKUPS": {
        # transforms don't need to be verbose, since their expressions are chained
        "date": _("date"),
        "year": _("year"),
        "month": _("month"),
        "day": _("day"),
        "week_day": _("week day"),
        "hour": _("hour"),
        "minute": _("minute"),
        "second": _("second"),
        # standard lookups
        "exact": "",
        "iexact": "",
        "contains": _("contains"),
        "icontains": _("contains"),
        "in": _("is in"),
        "gt": _("is greater than"),
        "gte": _("is greater than or equal to"),
        "lt": _("is less than"),
        "lte": _("is less than or equal to"),
        "startswith": _("starts with"),
        "istartswith": _("starts with"),
        "endswith": _("ends with"),
        "iendswith": _("ends with"),
        "range": _("is in range"),
        "isnull": _("is null"),
        "regex": _("matches regex"),
        "iregex": _("matches regex"),
        "search": _("search"),
        # postgres lookups
        "contained_by": _("is contained by"),
        "overlap": _("overlaps"),
        "has_key": _("has key"),
        "has_keys": _("has keys"),
        "has_any_keys": _("has any keys"),
        "trigram_similar": _("search"),
    },
}


DEPRECATED_SETTINGS = []


def is_callable(value):
    # check for callables, except types
    return callable(value) and not isinstance(value, type)


class Settings:
    def __getattr__(self, name):
        if name not in DEFAULTS:
            msg = "'%s' object has no attribute '%s'"
            raise AttributeError(msg % (self.__class__.__name__, name))

        value = self.get_setting(name)

        if is_callable(value):
            value = value()

        # Cache the result
        setattr(self, name, value)
        return value

    def get_setting(self, setting):
        django_setting = "FILTERS_%s" % setting

        if setting in DEPRECATED_SETTINGS and hasattr(dj_settings, django_setting):
            deprecate("The '%s' setting has been deprecated." % django_setting)

        return getattr(dj_settings, django_setting, DEFAULTS[setting])

    def change_setting(self, setting, value, enter, **kwargs):
        if not setting.startswith("FILTERS_"):
            return
        setting = setting[8:]  # strip 'FILTERS_'

        # ensure a valid app setting is being overridden
        if setting not in DEFAULTS:
            return

        # if exiting, delete value to repopulate
        if enter:
            setattr(self, setting, value)
        else:
            delattr(self, setting)


settings = Settings()
setting_changed.connect(settings.change_setting)
