"""opticsdiagram -- publication-quality optics layout diagrams with matplotlib.

The package exposes a single drawing canvas, :class:`OpticsDiagram`, with one method per
optical element. Build a layout by placing elements at chosen coordinates::

    from opticsdiagram import OpticsDiagram

    od = OpticsDiagram(figsize=(4, 3), component_size=0.22)
    od.laser(0.5, 1.5)
    od.laser_beam([(0.5, 1.5), (3.0, 1.5)])
    od.lens(2.0, 1.5, angle=90)
    od.photodiode(3.0, 1.5, angle=-90)
    od.savefig("layout.pdf")

The set of available elements is enumerated in :data:`COMPONENT_REGISTRY` (see also
:meth:`OpticsDiagram.list_components`), which drives the component gallery in the README.

The visual design of many elements was inspired by the gwoptics Component Library
(http://www.gwoptics.org/ComponentLibrary/).
"""

from .canvas import OpticsDiagram
from .registry import COMPONENT_REGISTRY, component

__version__ = "0.1.0"

__all__ = ["OpticsDiagram", "COMPONENT_REGISTRY", "component", "__version__"]
