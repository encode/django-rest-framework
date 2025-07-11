"""
Compatibility layer with Python 3.8/3.9
"""
from typing import TYPE_CHECKING, Any, Optional, Tuple

if TYPE_CHECKING:  # pragma: no cover
    # Prevent circular imports on runtime.
    from . import Distribution, EntryPoint
else:
    Distribution = EntryPoint = Any


def normalized_name(dist: Distribution) -> Optional[str]:
    """
    Honor name normalization for distributions that don't provide ``_normalized_name``.
    """
    try:
        return dist._normalized_name
    except AttributeError:
        from . import Prepared  # -> delay to prevent circular imports.

        return Prepared.normalize(getattr(dist, "name", None) or dist.metadata['Name'])


def ep_matches(ep: EntryPoint, **params) -> Tuple[EntryPoint, bool]:
    """
    Workaround for ``EntryPoint`` objects without the ``matches`` method.
    For the sake of convenience, a tuple is returned containing not only the
    boolean value corresponding to the predicate evalutation, but also a compatible
    ``EntryPoint`` object that can be safely used at a later stage.

    For example, the following sequences of expressions should be compatible:

        # Sequence 1: using the compatibility layer
        candidates = (_py39compat.ep_matches(ep, **params) for ep in entry_points)
        [ep for ep, predicate in candidates if predicate]

        # Sequence 2: using Python 3.9+
        [ep for ep in entry_points if ep.matches(**params)]
    """
    try:
        return ep, ep.matches(**params)
    except AttributeError:
        from . import EntryPoint  # -> delay to prevent circular imports.

        # Reconstruct the EntryPoint object to make sure it is compatible.
        _ep = EntryPoint(ep.name, ep.value, ep.group)
        return _ep, _ep.matches(**params)
