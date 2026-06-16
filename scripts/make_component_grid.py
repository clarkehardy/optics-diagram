"""Render a labelled gallery of every component in :mod:`opticsdiagram`.

Iterates the live ``COMPONENT_REGISTRY``, draws each registered element on its own small
canvas tiled into a single figure, and writes the result to ``assets/components.png``.
This image is embedded in the README so users can see, at a glance, what is available.

Run from anywhere::

    python scripts/make_component_grid.py
"""

import math
from pathlib import Path

import matplotlib.pyplot as plt

from opticsdiagram import OpticsDiagram, COMPONENT_REGISTRY

# Tile geometry. Each component is drawn on a 1x1 data canvas and placed at its centre;
# COMPONENT_SIZE is chosen so even the largest elements stay inside the tile.
TILE = 1.0
CENTER = TILE / 2
COMPONENT_SIZE = 0.16
NCOLS = 6

# Order categories sensibly; any category not listed falls to the end in first-seen order.
CATEGORY_ORDER = [
    "Sources",
    "Mirrors",
    "Beamsplitters",
    "Polarization",
    "Lenses",
    "Beam control",
    "Detectors",
    "Fibers & couplers",
    "Chambers & traps",
    "Electronics",
    "Markers",
]


def _ordered_entries():
    """Return registry items sorted by category (per ``CATEGORY_ORDER``) then insertion."""
    def sort_key(item):
        _, meta = item
        cat = meta["category"]
        rank = CATEGORY_ORDER.index(cat) if cat in CATEGORY_ORDER else len(CATEGORY_ORDER)
        return rank
    # Python's sort is stable, so within a category the registry (definition) order holds.
    return sorted(COMPONENT_REGISTRY.items(), key=sort_key)


def _draw_component(ax, meta):
    """Draw a single component, centered, onto ``ax`` using its registry demo spec."""
    od = OpticsDiagram(figsize=(TILE, TILE), component_size=COMPONENT_SIZE, ax=ax)
    demo = meta["demo"]
    if callable(demo):
        demo(od, CENTER, CENTER)
    else:
        getattr(od, meta["method"])(CENTER, CENTER, **demo)


def make_grid(outpath):
    """Build the component gallery and save it to ``outpath``."""
    entries = _ordered_entries()
    nrows = math.ceil(len(entries) / NCOLS)

    fig, axes = plt.subplots(
        nrows, NCOLS, figsize=(NCOLS * 1.7, nrows * 1.85), dpi=200,
    )
    axes = axes.ravel()

    for ax, (_, meta) in zip(axes, entries):
        _draw_component(ax, meta)
        ax.set_frame_on(True)
        for spine in ax.spines.values():
            spine.set_edgecolor("0.85")
        ax.text(
            0.5, -0.06, meta["display_name"], transform=ax.transAxes,
            ha="center", va="top", fontsize=9,
        )

    # Hide any unused tiles.
    for ax in axes[len(entries):]:
        ax.set_visible(False)

    fig.suptitle("opticsdiagram components", fontsize=14, fontweight="bold")
    fig.subplots_adjust(left=0.01, right=0.99, top=0.95, bottom=0.02, hspace=0.35, wspace=0.1)
    fig.savefig(outpath, dpi=200, bbox_inches="tight")
    print(f"Wrote {outpath} ({len(entries)} components)")


if __name__ == "__main__":
    out = Path(__file__).resolve().parent.parent / "assets" / "components.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    make_grid(out)
