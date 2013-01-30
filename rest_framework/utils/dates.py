def get_readable_date_format(date_format):
    mapping = [("%Y", "YYYY"),
               ("%y", "YY"),
               ("%m", "MM"),
               ("%b", "[Jan through Dec]"),
               ("%B", "[January through December]"),
               ("%d", "DD"),
               ("%H", "HH"),
               ("%M", "MM"),
               ("%S", "SS"),
               ("%f", "uuuuuu")]
    for k, v in mapping:
        date_format = date_format.replace(k, v)
    return date_format