"""Lightweight component registry for :mod:`opticsdiagram`.

Every placeable optical element is an ordinary method on
:class:`opticsdiagram.canvas.OpticsDiagram` that draws itself onto the canvas and
returns nothing. The registry adds *discoverability* on top of that design without
changing how elements are called: decorating a method with :func:`component` records a
small bit of metadata (a human-readable display name, a category, and the extra keyword
arguments needed to render a standalone demo of it) into the module-level
:data:`COMPONENT_REGISTRY`.

This metadata is what powers the component gallery (``scripts/make_component_grid.py``)
and :meth:`OpticsDiagram.list_components`. Helper methods and free-form drawing tools
(beams, wires, annotations, coordinate transforms) are deliberately *not* decorated, so
they never show up as standalone components.

A single drawing method can appear more than once in the gallery by stacking the
decorator with distinct ``key`` values -- this is how the half- and quarter-wave plate
variants of :meth:`OpticsDiagram.waveplate` each get their own tile.
"""

# Maps a registry key to component metadata, in registration order. Each value is a
# dict with keys:
#   ``method``       -- name of the OpticsDiagram method that draws it (str)
#   ``display_name`` -- human-readable label shown in the gallery (str)
#   ``category``     -- grouping used to organize the gallery (str)
#   ``demo``         -- extra keyword arguments for a standalone render (dict, may be {})
COMPONENT_REGISTRY = {}


def component(display_name, category, demo=None, key=None):
    """Register an :class:`OpticsDiagram` method as a placeable component.

    Intended to be used as a decorator on canvas methods at class-definition time. It
    records metadata in :data:`COMPONENT_REGISTRY` and returns the method unchanged, so
    decorating a method has no effect on how it is called. The decorator may be stacked
    to register several gallery variants of the same method (give each a distinct
    ``key``).

    Parameters
    ----------
    display_name : str
        Human-readable label for the component, e.g. ``"Polarizing beamsplitter"``.
        Shown beneath the element in the gallery.
    category : str
        Grouping used to organize the gallery, e.g. ``"Mirrors"`` or ``"Detectors"``.
    demo : dict or callable, optional
        How to render a standalone preview of the component. A dict supplies extra
        keyword arguments passed on top of the centre coordinates ``x, y`` (e.g.
        ``{"label": "DAQ"}`` for :meth:`OpticsDiagram.instrument`). A callable takes
        ``(canvas, x, y)`` and draws the preview itself -- used for components whose
        signature needs positional context, such as a chamber's viewport coordinates or
        a wire path. Defaults to an empty dict.
    key : str, optional
        Registry key for this entry. Defaults to the method name. Supply an explicit
        key when registering a second variant of an already-registered method so the
        entries do not collide.

    Returns
    -------
    callable
        The original, undecorated method.
    """
    def decorator(func):
        if demo is None:
            demo_spec = {}
        elif callable(demo):
            demo_spec = demo
        else:
            demo_spec = dict(demo)
        COMPONENT_REGISTRY[key or func.__name__] = {
            "method": func.__name__,
            "display_name": display_name,
            "category": category,
            "demo": demo_spec,
        }
        return func

    return decorator
