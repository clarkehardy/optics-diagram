"""Levitated-nanosphere trapping and readout layout.

A compact optical layout for a levitated-nanosphere experiment: a 1064 nm trapping beam
conditioned by an EOM, wave plates and polarizing beamsplitters, a perpendicular 266 nm
beam, the trapped sphere inside an octagonal vacuum chamber, photodiode readout, and the
feedback/DAQ electronics. Reproduces the figure used for the Neutrino 2026 conference.

Run with::

    python examples/nanosphere_setup.py
"""

from pathlib import Path

from opticsdiagram import OpticsDiagram

OUTDIR = Path(__file__).resolve().parent / "output"
OUTDIR.mkdir(parents=True, exist_ok=True)

x_sphere = 2.65
y_sphere = 1.5

component_size = 0.22
beam_width = 0.4 * component_size
fontsize = 8
od = OpticsDiagram((4, 3), component_size, fontsize, check_frame=False)

od.octagonal_chamber(x_sphere, y_sphere, 0.7, angle=0, viewports=(True, True, True, True))
od.lens(x_sphere - 0.2, y_sphere, angle=0)
od.lens_holder(x_sphere - 0.2, y_sphere, angle=0)
od.lens(x_sphere + 0.2, y_sphere, angle=0)
od.lens_holder(x_sphere + 0.2, y_sphere, angle=0)

od.cube_bs(x_sphere - 1.0, y_sphere)
od.annotation(x_sphere - 1.0, y_sphere + 0.2, 'PBS', ha='center', va='bottom')
od.laser_beam(((x_sphere - 1.0, y_sphere), (x_sphere - 1.0, y_sphere - 0.3)), beam_width, alpha=0.3)

od.collimator(x_sphere - 1.0, y_sphere - 0.3, 90)
od.wire(((x_sphere - 1.0, y_sphere - 0.4), (x_sphere - 1.0, y_sphere - 0.5), (x_sphere - 1.0, y_sphere - 0.7), \
         (x_sphere - 0.9, y_sphere - 0.7), (x_sphere - 0.4, y_sphere - 0.7)), \
        round_corners=(False, False, True, False, False), color='dodgerblue')

od.coupler(x_sphere - 0.7, y_sphere - 0.7, angle=90)

od.waveplate(x_sphere - 2.0, y_sphere, quarter=True, angle=0)
od.annotation(x_sphere - 2.0, y_sphere + 0.2, 'QWP', ha='center', va='bottom')
od.eom(x_sphere - 1.75, y_sphere)
od.annotation(x_sphere - 1.75, y_sphere - 0.2, 'EOM', ha='center', va='top')
od.cube_bs(x_sphere - 1.4, y_sphere)
od.annotation(x_sphere - 1.4, y_sphere + 0.2, 'PBS', ha='center', va='bottom')

od.laser_beam(((x_sphere - 1.4, y_sphere), (x_sphere - 1.4, y_sphere - 0.4)), beam_width, alpha=0.3)
od.beam_dump(x_sphere - 1.4, y_sphere - 0.35, angle=90)

od.waveplate(x_sphere - 1.2, y_sphere)
od.annotation(x_sphere - 1.2, y_sphere - 0.2, 'HWP', ha='center', va='top')

od.circulator(x_sphere - 0.7, y_sphere, 0, reflected=True)

od.collimator(x_sphere - 0.7, y_sphere - 0.3, 90)
od.wire(((x_sphere - 0.7, y_sphere - 0.4), (x_sphere - 0.7, y_sphere - 1)), color='dodgerblue')

od.photodiode(x_sphere - 0.4, y_sphere - 0.7, angle=-180)
od.photodiode(x_sphere - 0.7, y_sphere - 1, angle=90)

od.microsphere(x_sphere, y_sphere)

od.laser(x_sphere - 2.1, y_sphere, 0)
od.annotation(x_sphere - 2.1, y_sphere - 0.2, '1064 nm', ha='right', va='top')

od.laser(x_sphere, y_sphere + 0.7, color='violet', angle=-90)
od.annotation(x_sphere - 0.2, y_sphere + 0.9, '266 nm', ha='right', va='center')

od.lens(x_sphere, y_sphere + 0.5, angle=-90)
od.laser_beam(((x_sphere, y_sphere + 0.7), (x_sphere, y_sphere - 0.6)), color='violet', width=0.1 * component_size)
od.beam_dump(x_sphere, y_sphere - 0.5, 90)

od.wire(((x_sphere - 0.7, y_sphere - 1.1), (x_sphere - 0.7, y_sphere - 1.2), (x_sphere - 0.6, y_sphere - 1.3), (x_sphere + 0.2, y_sphere - 1.3)))
od.wire(((x_sphere - 0.3, y_sphere - 0.7), (x_sphere - 0.2, y_sphere - 0.7), (x_sphere - 0.1, y_sphere - 0.8), (x_sphere - 0.1, y_sphere - 1.3)))
od.operation(x_sphere - 0.1, y_sphere - 1.3, '-')

od.instrument(x_sphere + 0.2 + component_size * 0.75, y_sphere - 1.3, 'DAQ')
od.instrument(x_sphere + 1, y_sphere, '$x$, $y$, $z$ \nfeedback', width=3 * component_size, height=2 * component_size)
od.wire(((x_sphere + 1, y_sphere + component_size), (x_sphere + 1, y_sphere + 1.3), (x_sphere - 1.75, y_sphere + 1.3), (x_sphere - 1.75, y_sphere + 0.5 * component_size)), arrow=True)
od.filament(x_sphere + 1.0 * component_size, y_sphere - 1.4 * component_size, angle=45)

od.needle(x_sphere - 0.6 * component_size, y_sphere - 1.0 * component_size, -45)

od.ac_source(x_sphere + 0.6, y_sphere + 0.4, ((x_sphere + 0.2, y_sphere + 0.4), (x_sphere + 0.2, y_sphere + 0.75 * component_size)), connection='left', angle=0)
od.ground(x_sphere - 0.5, y_sphere + 0.3, ((x_sphere - 0.5, y_sphere + 0.4), (x_sphere - 0.2, y_sphere + 0.4), (x_sphere - 0.2, y_sphere + 0.75 * component_size)))

od.laser_beam(((x_sphere - 2.1, y_sphere), (x_sphere - 0.2, y_sphere)), width=beam_width, alpha=0.3)
od.laser_beam(((x_sphere - 0.7, y_sphere), (x_sphere - 0.7, y_sphere - 0.3)), width=beam_width, alpha=0.3)
od.focused_beam((x_sphere - 0.2, y_sphere), (x_sphere + 0.2, y_sphere), beam_width, beam_width, alpha=0.3, show_focus=True)
od.laser_beam(((x_sphere + 0.2, y_sphere), (x_sphere + 1 - 0.5 * component_size, y_sphere)), beam_width, alpha=0.3)

od.compass(x_sphere + 0.7, y_sphere - 0.9, angle=0)
od.annotation(x_sphere + 0.7 + 1.1 * component_size, y_sphere - 0.95, '$z$', ha='left', va='top')
od.annotation(x_sphere + 0.7 - 0.15 * component_size, y_sphere - 0.6, '$x$', ha='right', va='top')
od.annotation(x_sphere + 0.7 - 0.15 * component_size, y_sphere - 0.95, '$y$', ha='right', va='top')

od.savefig(OUTDIR / 'nanosphere_setup.png', dpi=300, pad_inches=0.0)
od.savefig(OUTDIR / 'nanosphere_setup.pdf')
print(f"Wrote {OUTDIR / 'nanosphere_setup.png'} and .pdf")
