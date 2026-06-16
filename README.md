# opticsdiagram

Publication-quality optics layout diagrams with [matplotlib](https://matplotlib.org/).

`opticsdiagram` provides a single drawing canvas, `OpticsDiagram`, with one method per
optical element — mirrors, lenses, beamsplitters, wave plates, photodiodes, vacuum
chambers, and more. You build a layout by placing elements at chosen coordinates and
connecting them with beams and wires. Everything is drawn in shared data coordinates, so
positioning a setup is just simple arithmetic on a grid.

![Component gallery](assets/components.png)

## Installation

Install the latest version directly from GitHub:

```bash
pip install git+https://github.com/clarkehardy/optics-diagram.git
```

Or clone and install in editable mode for development:

```bash
git clone https://github.com/clarkehardy/optics-diagram.git
cd optics-diagram
pip install -e .
```

The only dependencies are `numpy` and `matplotlib`.

## Quickstart

```python
from opticsdiagram import OpticsDiagram

# A canvas 4 x 3 inches; one data unit = one inch.
od = OpticsDiagram(figsize=(4, 3), component_size=0.22, fontsize=8)

od.laser(0.6, 1.5)
od.annotation(0.6, 1.2, "1064 nm", ha="center", va="top")

od.waveplate(1.4, 1.5)
od.cube_bs(2.0, 1.5)
od.lens(2.6, 1.5, angle=90)
od.photodiode(3.3, 1.5, angle=-90)

od.laser_beam([(0.6, 1.5), (3.3, 1.5)])

od.savefig("layout.pdf")
```

Every placeable element is a method called as `od.<element>(x, y, angle=...)`. Elements
draw themselves onto the canvas and return nothing — you place one where you want it
(optionally tweaking the position or angle) and move on. Position, `component_size`, and
beam paths are all in the same data units as the axis limits.

## Available components

The image at the top of this README is generated from the live component registry by
[`scripts/make_component_grid.py`](scripts/make_component_grid.py) — every element in the
package appears there with its name. To regenerate it:

```bash
python scripts/make_component_grid.py
```

You can also enumerate the components programmatically:

```python
from opticsdiagram import COMPONENT_REGISTRY
for key, meta in COMPONENT_REGISTRY.items():
    print(meta["category"], "—", meta["display_name"])
```

In addition to the placeable components, the canvas provides drawing tools that are not
single elements: `laser_beam` and `focused_beam` (beam paths), `wire` (cables, with
optional rounded corners and arrowheads), `annotation` (labels with optional arrows),
`section_view` (cut-away boxes), and helpers such as `rotate`, `apply_gradient`, and
`data_to_points`.

## Examples

Full, runnable diagrams from real experiments live in [`examples/`](examples/):

- [`examples/nanosphere_setup.py`](examples/nanosphere_setup.py) — a levitated-nanosphere
  trapping and readout layout.
- [`examples/microsphere_setup.py`](examples/microsphere_setup.py) — a detailed
  microsphere interferometric readout layout with input/output optics, vacuum chamber,
  and a section view.

Each script writes its figure to `examples/output/`.

## Acknowledgements

The visual design of many of the components was inspired by the excellent
[gwoptics Component Library](http://www.gwoptics.org/ComponentLibrary/), a set of
optical-layout drawing primitives from the gravitational-wave optics group.
