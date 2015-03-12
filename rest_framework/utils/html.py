"""
Helpers for dealing with HTML input.
"""
import re


def is_html_input(dictionary):
    # MultiDict type datastructures are used to represent HTML form input,
    # which may have more than one value for each key.
    return hasattr(dictionary, 'getlist')


def parse_json_form(dictionary, prefix=''):
    """
    Parse an HTML JSON form submission as per the W3C Draft spec
    An implementation of "The application/json encoding algorithm"
    http://www.w3.org/TR/html-json-forms/
    """
    # Step 1: Initialize output object
    output = {}
    for name, value in get_all_items(dictionary):
        # TODO: implement is_file flag

        # Step 2: Compute steps array
        steps = parse_json_path(name)

        # Step 3: Initialize context
        context = output

        # Step 4: Iterate through steps
        for step in steps:
            # Step 4.1 Retrieve current value from context
            current_value = get_value(context, step.key, Undefined())

            # Steps 4.2, 4.3: Set JSON value on context
            context = set_json_value(
                context=context,
                step=step,
                current_value=current_value,
                entry_value=value,
                is_file=False,
            )
    # Convert any remaining Undefined array entries to None
    output = clean_undefined(output)

    # Account for DRF prefix (not part of JSON form spec)
    result = get_value(output, prefix, Undefined())
    if isinstance(result, Undefined):
        return output
    else:
        return result


def parse_json_path(path):
    """
    Parse a string as a JSON path
    An implementation of "steps to parse a JSON encoding path"
    http://www.w3.org/TR/html-json-forms/#dfn-steps-to-parse-a-json-encoding-path
    """

    # Steps 1, 2, 3
    original_path = path
    steps = []

    # Step 11 (Failure)
    failed = [
        JsonStep(
            type="object",
            key=original_path,
            last=True,
            failed=True,
        )
    ]

    # Other variables for later use
    digit_re = re.compile(r'^\[([0-9]+)\]')
    key_re = re.compile(r'^\[([^\]]+)\]')

    # Step 4 - Find characters before first [ (if any)
    parts = path.split("[")
    first_key = parts[0]
    if parts[1:]:
        path = "[" + "[".join(parts[1:])
    else:
        path = ""

    # Step 5 - According to spec, keys cannot start with [
    # NOTE: This was allowed in older DRF versions, so disabling rule for now
    # if not first_key:
    #     return failed

    # Step 6 - Save initial step
    steps.append(JsonStep(
        type="object",
        key=first_key,
    ))

    # Step 7 - Simple single-step case (no [ found)
    if not path:
        steps[-1].last = True
        return steps

    # Step 8 - Loop
    while path:
        # Step 8.1 - Check for single-item array
        if path[:2] == "[]":
            steps[-1].append = True
            path = path[2:]
            if path:
                return failed
            continue

        # Step 8.2 - Check for array[index]
        digit_match = digit_re.match(path)
        if digit_match:
            path = digit_re.sub("", path)
            steps.append(JsonStep(
                type="array",
                key=int(digit_match.group(1)),
            ))
            continue

        # Step 8.3 - Check for object[key]
        key_match = key_re.match(path)
        if key_match:
            path = key_re.sub("", path)
            steps.append(JsonStep(
                type="object",
                key=key_match.group(1),
            ))
            continue

        # Step 8.4 - Invalid key format
        return failed

    # Step 9
    next_step = None
    for step in reversed(steps):
        if next_step:
            step.next_type = next_step.type
        else:
            step.last = True
        next_step = step

    return steps


def set_json_value(context, step, current_value, entry_value, is_file):
    """
    Apply a JSON value to a context object
    An implementation of "steps to set a JSON encoding value"
    http://www.w3.org/TR/html-json-forms/#dfn-steps-to-set-a-json-encoding-value
    """

    # TODO: handle is_file

    # Add empty values to array so indexing works like JavaScript
    if isinstance(context, list) and isinstance(step.key, int):
        while len(context) <= step.key:
            context.append(Undefined())

    # Step 7: Handle last step
    if step.last:
        if isinstance(current_value, Undefined):
            # Step 7.1: No existing value
            key = step.key
            if isinstance(context, dict) and isinstance(key, int):
                key = str(key)
            if step.append:
                context[key] = [entry_value]
            else:
                context[key] = entry_value
        elif isinstance(current_value, list):
            # Step 7.2: Existing value is an Array, assume multi-valued field
            # and add entry to end.

            # FIXME: What if the other items in the array had explicit keys and
            # this one is supposed to be the "" value?
            # (See step 8.4 and Example 7)
            context[step.key].append(entry_value)

        elif isinstance(current_value, dict) and not is_file:
            # Step 7.3: Existing value is an Object
            return set_json_value(
                context=current_value,
                step=JsonStep(type="object", key="", last=True),
                current_value=current_value.get("", Undefined()),
                entry_value=entry_value,
                is_file=is_file,
            )
        else:
            # Step 7.4: Existing value is a scalar; preserve both values
            context[step.key] = [current_value, entry_value]

        # Step 7.5
        return context

    # Step 8: Handle intermediate steps
    if isinstance(current_value, Undefined):
        # 8.1: No existing value
        if step.next_type == "array":
            context[step.key] = []
        else:
            context[step.key] = {}
        return context[step.key]
    elif isinstance(current_value, dict):
        # Step 8.2: Existing value is an Object
        return get_value(context, step.key, Undefined())
    elif isinstance(current_value, list):
        # Step 8.3: Existing value is an Array
        if step.next_type == "array":
            return current_value
        # Convert array to object to facilitate mixed keys
        obj = {}
        for i, item in enumerate(current_value):
            if not isinstance(item, Undefined):
                obj[str(i)] = item
        context[step.key] = obj
        return obj
    else:
        # 8.4: Existing value is a scalar; convert to Object, preserving
        # current value via an empty key
        obj = {'': current_value}
        context[step.key] = obj
        return obj


def get_value(obj, key, default=None):
    """
    Mimic JavaScript Object/Array behavior by allowing access to nonexistent
    indexes.
    """
    if isinstance(obj, dict):
        return obj.get(key, default)
    elif isinstance(obj, list):
        try:
            return obj[key]
        except IndexError:
            return default


class Undefined(object):
    """
    Use Undefined() rather than None to distinguish from null.
    """
    pass


class JsonStep(object):
    """
    Struct to represent "step" as described in HTML JSON form algorithm
    """
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __repr__(self):
        vals = ",".join(
            "%s=%s" % (key, val) for key, val in self.__dict__.items()
        )
        return "JsonStep(%s)" % vals

    type = None
    next_type = None
    key = None
    append = None
    last = None
    failed = None


def clean_undefined(obj):
    """
    Convert Undefined array entries to None (null)
    """
    if isinstance(obj, list):
        return [
            None if isinstance(item, Undefined) else item
            for item in obj
        ]
    if isinstance(obj, dict):
        for key in obj:
            obj[key] = clean_undefined(obj[key])
    return obj


def get_all_items(obj):
    """
    dict.items() but with a separate row for each value in a MultiValueDict
    """
    if hasattr(obj, 'getlist'):
        items = []
        for key in obj:
            for value in obj.getlist(key):
                items.append((key, value))
        return items
    else:
        return obj.items()
