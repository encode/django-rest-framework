from datetime import datetime, timezone, tzinfo


def datetime_exists(dt):
    """Check if a datetime exists. Taken from: https://pytz-deprecation-shim.readthedocs.io/en/latest/migration.html"""
    # There are no non-existent times in UTC, and comparisons between
    # aware time zones always compare absolute times; if a datetime is
    # not equal to the same datetime represented in UTC, it is imaginary.
    return dt.astimezone(timezone.utc) == dt


def datetime_ambiguous(dt: datetime):
    """Check whether a datetime is ambiguous. Taken from: https://pytz-deprecation-shim.readthedocs.io/en/latest/migration.html"""
    # If a datetime exists and its UTC offset changes in response to
    # changing `fold`, it is ambiguous in the zone specified.
    return datetime_exists(dt) and (
        dt.replace(fold=not dt.fold).utcoffset() != dt.utcoffset()
    )


def valid_datetime(dt):
    """Returns True if the datetime is not ambiguous or imaginary, False otherwise."""
    if isinstance(dt.tzinfo, tzinfo) and not datetime_ambiguous(dt):
        return True
    return False
