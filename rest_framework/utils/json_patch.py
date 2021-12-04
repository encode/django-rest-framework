from jsonpatch import (
    InvalidJsonPatch,
    JsonPatchConflict,
    JsonPatchTestFailed,
    JsonPointerException,
)

from rest_framework.exceptions import ValidationError, ParseError


def filter_state(state, paths_parts):
    filtered_state = {}
    for parts in paths_parts:
        if len(parts) > 1:
            parts = iter(parts)
            next_part = next(parts)
            parts = [list(parts)]
            filtered_state[next_part] = filter_state(state[next_part], parts)
        elif len(parts) == 1:
            filtered_state[parts[0]] = state[parts[0]]
        else:
            # empty parts will raise JsonPointerException during apply()
            # this type of error should be checked by json_patch at the
            # initilization not during the application.
            continue

    return filtered_state


def apply_json_patch(patch, current_state):
    field = None
    try:
        # empty parts will raise JsonPointerException during apply()
        # this type of error should be checked by json_patch at the
        # initilization not during the application.
        paths_parts = [[part for op in patch._ops for part in op.pointer.parts if part]]
        filtered_state = filter_state(current_state, paths_parts)
        return patch.apply(filtered_state)
    except KeyError:
        raise ValidationError(
            {'details': f'JSON Patch (rfc 6902) path does not exist - {field}'}
        )
    except JsonPatchConflict as exc:
        raise ValidationError({'details': f'JSON Patch (rfc 6902) conflict - {exc}'})
    except JsonPatchTestFailed as exc:
        raise ValidationError({'details': f'JSON Patch (rfc 6902) test failed - {exc}'})
    except JsonPointerException as exc:
        raise ValidationError(
            {'details': f"JSON Patch (rfc 6902) path's part invalid - {exc}"}
        )
    except InvalidJsonPatch as exc:
        raise ParseError(f'JSON Patch (rfc 6902) invalid - {exc}')
