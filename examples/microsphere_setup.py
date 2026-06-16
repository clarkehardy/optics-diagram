"""Microsphere interferometric readout layout.

A detailed optical layout for a levitated-microsphere experiment: input fiber and
polarization conditioning, a pickoff and power monitor, a piezo deflector, a telescope
into the vacuum chamber, the trapped sphere in its electrode cube (with an orthogonal
section view through the parabolic mirrors), and the output optics feeding heterodyne
and DC quadrant photodiodes, cameras and transmitted-power detectors. Reproduces the
optics schematic from the modified-gravity chapter of the author's PhD thesis.

Run with::

    python examples/microsphere_setup.py
"""

from pathlib import Path

from opticsdiagram import OpticsDiagram

OUTDIR = Path(__file__).resolve().parent / "output"
OUTDIR.mkdir(parents=True, exist_ok=True)

# Horizontal positions of the optical elements (left to right).
x_back_cam = 0.2
x_bs_dump = 0.2
x_wp_far_1 = 0.4
x_bs_far_1 = 0.6
x_trap_wp = 0.8
x_z_pd = 1.0
x_wp_far_2 = 1.3
x_bs_far_2 = 1.5
x_piezo = 1.8
x_lens_1 = 2.1
x_lens_2 = 2.4
x_sphere = 2.95
x_prism_mirror = 3.45
x_lens_3 = 3.8
x_aperture = 4.0
x_lens_4 = 4.1
x_pellicle = 4.4
x_het_qpd = 4.8
x_dc_qpd = 5.45
x_trans_pd = 5.75
x_bs_forwardcam = 5.15
x_het_ref = 5.6
x_led = 4.4
x_spin_pd = 4.4

# Vertical positions of the optical elements.
y_z_pd = 0.2
y_back_cam = 0.8
y_input_pd = 1.4
y_spin_pd = 3.4
y_piezo = 2.0
y_s_dump = 2.2
y_trap = 3.0
y_het_ref = 0.35
y_sphere = 2.0
y_aperture = 2.0
y_forward_cam = 1.1
y_bs_row = 2.4
y_trans_pd = 2.9
y_qpd = 3.1
y_s_port = 2.7
y_top_cam = 3.6

# Geometry of the chamber section view.
sec_offset = -1.2
sec_height = 1.4
sec_width = 0.65
parab_offset = 0.5

component_size = 0.22
beam_width = 0.05
fontsize = 8
led_alpha = 0.2
od = OpticsDiagram((6, 4), component_size, fontsize, check_frame=False)

# INPUT FIBER AND POLARIZATION MAINTENANCE
od.collimator(x_z_pd, y_trap, 180, fiber=True, reflected=True)
od.annotation(x_z_pd + 0.4, y_trap - 0.1, 'Trap beam', ha='left', va='center')
od.polarizer(x_trap_wp, y_trap)
od.annotation(x_trap_wp, y_trap + 0.15, 'Polarizer', ha='left', va='bottom')
od.waveplate(x_bs_far_1, y_trap)
od.annotation(x_bs_far_1, y_trap + 0.15, 'HWP', ha='center', va='bottom')
od.mirror(x_bs_dump, y_trap, angle=-45)
od.cube_bs(x_bs_dump, y_s_dump, 90)
od.annotation(x_bs_dump + 0.15, y_s_dump, 'PBS', ha='left', va='center')
od.mirror(x_bs_dump, y_input_pd, angle=45)
od.laser_beam(((x_z_pd, y_trap), (x_bs_dump, y_trap), (x_bs_dump, y_input_pd), \
               (x_lens_1, y_input_pd)), beam_width)

# REFERENCE BEAM AND ZPD
od.beamsplitter(x_bs_far_1, y_back_cam, -45)
od.annotation(x_bs_far_1 - 0.05, y_back_cam + 0.1, 'BS', ha='right', va='bottom')
od.collimator(x_z_pd, y_back_cam, 180, fiber=True, reflected=True)
od.annotation(x_z_pd + 0.4, y_back_cam - 0.1, 'Ref. beam', ha='left', va='center')
od.waveplate(x_trap_wp, y_back_cam)
od.annotation(x_trap_wp, y_back_cam + 0.15, 'HWP', ha='center', va='bottom')
od.mirror(x_bs_far_1, y_z_pd, angle=45)
od.photodiode(x_z_pd, y_z_pd, angle=-180)
od.annotation(x_z_pd + 0.2, y_z_pd, '$z$ PD', ha='left', va='center')
od.camera(x_back_cam, y_back_cam, 0)
od.laser_beam(((x_bs_far_1, y_input_pd), (x_bs_far_1, y_z_pd), (x_z_pd, y_z_pd)), beam_width)  # to ZPD
od.laser_beam(((x_bs_far_1, y_back_cam), (x_z_pd, y_back_cam)), beam_width)  # reference beam
od.laser_beam(((x_back_cam, y_back_cam), (x_bs_far_1, y_back_cam)), beam_width)  # to back refl. camera
od.annotation(x_back_cam - 0.15, y_back_cam - 0.2, 'Back\nrefl.\ncamera', ha='left', va='top')

# INPUT BEAM AND PICKOFF
od.waveplate(x_wp_far_1, y_input_pd)
od.annotation(x_wp_far_1, y_input_pd - 0.15, 'HWP', ha='center', va='top')
od.cube_bs(x_bs_far_1, y_input_pd, 90)
od.annotation(x_bs_far_1, y_input_pd + 0.15, 'PBS', ha='center', va='bottom')
od.faraday_rotator(x_z_pd, y_input_pd)
od.annotation(x_z_pd, y_input_pd + 0.15, 'Faraday\nrotator', ha='center', va='bottom')
od.waveplate(x_wp_far_2, y_input_pd)
od.annotation(x_wp_far_2, y_input_pd - 0.15, 'HWP', ha='center', va='top')
od.cube_bs(x_bs_far_2, y_input_pd)
od.annotation(x_bs_far_2, y_input_pd + 0.15, 'PBS', ha='center', va='bottom')
od.beamsplitter(x_piezo, y_input_pd, angle=-45)
od.annotation(x_piezo, y_input_pd - 0.15, '90:10', ha='center', va='top')
od.photodiode(x_lens_1, y_input_pd, -180)
od.annotation(x_lens_1 + 0.1, y_input_pd - 0.15, 'Input\npower PD', ha='center', va='top')
od.piezo_deflector(x_piezo, y_piezo, angle=-45, reflected=False)
od.annotation(x_piezo - 0.15, y_piezo + 0.15, 'Piezo\ndeflector', ha='center', va='bottom')
od.laser_beam(((x_piezo, y_input_pd), (x_piezo, y_piezo), (x_lens_1, y_piezo)), beam_width)

# ENTERING THE VACUUM CHAMBER
od.lens(x_lens_1, y_piezo, angle=0)
od.annotation(x_lens_1 + 0.15, y_piezo - 0.1, '1:4\ntelescope', ha='center', va='top')
od.lens(x_lens_2, y_piezo, angle=0)
od.focused_beam((x_lens_1, y_piezo), (x_lens_2, y_piezo), beam_width, 2 * beam_width)
od.laser_beam(((x_lens_2, y_piezo), (x_sphere - component_size, y_piezo)), 2 * beam_width)

# INSIDE THE VACUUM CHAMBER
od.vacuum_chamber(x_sphere + 0.15, (y_s_port + y_aperture)/2 + 0.0, \
                  1.1, 1.9*(y_s_port - y_aperture), 0, \
                  ((x_sphere - 0.4, y_piezo), (x_sphere + 0.7, y_s_port), \
                   (x_sphere + 0.7, y_aperture), \
                   (x_sphere, 1.45*y_s_port - 0.45*y_aperture + 0.0, 90)))
od.annotation(x_sphere - 0.5, y_sphere + 0.15, 'Vacuum chamber', ha='center', va='bottom', \
              rotation=90)
od.microsphere(x_sphere, y_sphere)
od.electrode_cube(x_sphere, y_sphere)
od.cube_bs(x_prism_mirror, y_aperture, -90)
od.annotation(x_prism_mirror, y_aperture - 0.15, 'PBS', ha='center', va='top')
od.prism_mirror(x_prism_mirror, y_s_port, angle=90)
od.annotation(x_prism_mirror, y_s_port, 'Prism\nmirror', ha='right', va='bottom')

# SECTION VIEW OF THE CHAMBER
od.section_view(x_sphere, y_sphere, sec_width, sec_height, sec_offset - sec_height/2)
od.parabolic_mirror(x_sphere, y_sphere + sec_offset - parab_offset, 180, reflected=True)
od.parabolic_mirror(x_sphere, y_sphere + sec_offset + parab_offset, 0, reflected=True)
od.annotation(4.0, 0.6, 'Parabolic mirror', \
              arrow_pos=(x_sphere + 0.2, y_sphere + sec_offset - parab_offset), \
              ha='center', va='center')
od.microsphere(x_sphere, y_sphere + sec_offset)
od.electrode_cube(x_sphere, y_sphere + sec_offset)
od.annotation(1.9, 0.4, 'Electrode cube', arrow_pos=(x_sphere - 0.25, y_sphere + sec_offset), \
              ha='center', va='center')
od.laser_beam(((x_sphere, y_sphere + sec_offset + parab_offset), \
               (x_sphere + sec_width/2, y_sphere + sec_offset + parab_offset)), \
              3*beam_width, color='darkred', alpha=led_alpha)
od.focused_beam((x_sphere, y_sphere + sec_offset + parab_offset), \
                (x_sphere, y_sphere + sec_offset), 3*beam_width, beam_width, \
                color='darkred', alpha=led_alpha, show_focus=False)
od.focused_beam((x_sphere, y_sphere + sec_offset - parab_offset + beam_width), \
                (x_sphere, y_sphere + sec_offset + parab_offset - beam_width), \
                2*beam_width, 2*beam_width)
od.laser_beam(((x_sphere - sec_width/2, y_sphere + sec_offset - parab_offset), \
               (x_sphere, y_sphere + sec_offset - parab_offset)), \
              2*beam_width)
od.laser_beam(((x_sphere, y_sphere + sec_offset + parab_offset), \
               (x_sphere + sec_width/2, y_sphere + sec_offset + parab_offset)), \
              2*beam_width)

# EXITING THE VACUUM CHAMBER
od.laser_beam(((x_sphere + component_size, y_aperture), (x_prism_mirror, y_aperture), \
               (x_prism_mirror, y_s_port), (x_aperture + 0.2, y_s_port), \
               (x_aperture + 0.2, y_top_cam)), 3*beam_width, \
              color='darkred', alpha=led_alpha)
od.laser_beam(((x_aperture - 0.1, y_s_port + beam_width), (x_aperture - 0.1, y_s_port + 0.3)), \
              3*beam_width, color='darkred', alpha=led_alpha)
od.laser_beam(((x_sphere + component_size, y_aperture), (x_lens_3, y_aperture)), 2*beam_width)
od.focused_beam((x_lens_3, y_aperture), (x_lens_4, y_aperture), 2*beam_width, beam_width)

# OUTPUT OPTICS LEFT TO RIGHT
od.lens(x_lens_3, y_aperture, 0)
od.annotation(x_lens_3 + 0.2, y_aperture + 0.15, '4:1 \ntelescope', ha='center', va='bottom')
od.aperture(x_aperture, y_aperture, 0)
od.annotation(x_aperture, 1.3, r'50 $\mu$m aperture', arrow_pos=(x_aperture, y_aperture - 0.15), \
              ha='center', va='top')
od.lens(x_lens_4, y_aperture, 0)
od.pellicle(x_pellicle, y_aperture, -45)
od.annotation(x_pellicle, y_aperture - 0.15, '45:55\npellicle\nBS', ha='center', va='top')
od.mirror(x_pellicle, y_bs_row, -45)
od.mirror(x_het_qpd, y_het_ref, 45)
od.beamsplitter(x_bs_forwardcam, y_bs_row, 45)
od.annotation(x_bs_forwardcam, y_bs_row + 0.15, '8:92', ha='center', va='bottom')
od.mirror(x_bs_forwardcam, y_forward_cam, 45)
od.beamsplitter(x_dc_qpd, y_bs_row, -45)
od.annotation(x_dc_qpd, y_bs_row - 0.15, 'BS', ha='center', va='top')
od.beamsplitter(x_trans_pd, y_bs_row, -45)
od.annotation(x_trans_pd, y_bs_row - 0.15, 'BS', ha='center', va='top')
od.beam_dump(x_trans_pd + 0.12, y_bs_row, 180)
od.laser_beam(((x_trans_pd, y_bs_row), (x_trans_pd + 0.12, y_bs_row)), beam_width)
od.photodiode(x_trans_pd, y_trans_pd, -90)
od.annotation(x_trans_pd + 0.05, y_trans_pd + 0.15, 'Trans.\npower\nPD', ha='center', va='bottom')
od.diffuser(x_dc_qpd, y_forward_cam)
od.annotation(x_dc_qpd, y_forward_cam + 0.15, 'Phase\ndiffuser', ha='center', va='bottom')
od.camera(x_trans_pd, y_forward_cam, 180)
od.annotation(x_trans_pd + 0.15, y_forward_cam - 0.15, 'Forward\ncamera', ha='right', va='top')
od.qpd(x_dc_qpd, y_qpd, -90)
od.annotation(x_dc_qpd, y_qpd + 0.45, 'DC QPD', ha='center', va='bottom')

# REFERENCE BEAM OPTICS
od.collimator(x_het_ref, y_het_ref, 180, fiber=True, reflected=True)
od.annotation(x_het_ref + 0.1, y_het_ref - 0.2, 'Ref. beam', ha='center', va='top')
od.waveplate(x_het_ref - 0.15, y_het_ref)
od.annotation(x_het_ref - 0.15, y_het_ref + 0.15, 'HWP', ha='center', va='bottom')
od.cube_bs(x_het_ref - 0.35, y_het_ref)
od.annotation(x_het_ref - 0.35, y_het_ref - 0.15, 'PBS', ha='center', va='top')
od.beamsplitter(x_het_qpd, y_aperture, -45)
od.annotation(x_het_qpd - 0.05, y_aperture + 0.05, 'BS', ha='right', va='bottom')
od.beam_dump(x_het_qpd + 0.15, y_aperture, 180)
od.qpd(x_het_qpd, y_qpd, -90)
od.annotation(x_het_qpd, y_qpd + 0.45, 'Het. QPD', ha='center', va='bottom')

# OUTPUT LASER BEAMS
od.laser_beam(((x_lens_4, y_aperture), (x_het_qpd, y_aperture), \
               (x_het_qpd + 0.15, y_aperture)), beam_width)
od.laser_beam(((x_pellicle, y_aperture), (x_pellicle, y_bs_row), (x_dc_qpd, y_bs_row), \
               (x_dc_qpd, y_qpd)), beam_width)
od.laser_beam(((x_het_ref, y_het_ref), (x_het_qpd, y_het_ref), (x_het_qpd, y_qpd)), beam_width)
od.laser_beam(((x_trans_pd, y_trans_pd), (x_trans_pd, y_bs_row), (x_bs_forwardcam, y_bs_row), \
               (x_bs_forwardcam, y_forward_cam), (x_trans_pd, y_forward_cam)), beam_width)

# S-POLARIZED PORT BEAMS
od.laser_beam(((x_prism_mirror, y_aperture), (x_prism_mirror, y_s_port), (x_aperture + 0.2, y_s_port), \
               (x_aperture + 0.2, y_spin_pd), (x_spin_pd, y_spin_pd)), 2*beam_width)

# S-POLARIZED PORT OPTICS
od.cube_bs(x_aperture - 0.1, y_s_port, -90, block_beam=False)
od.annotation(x_aperture - 0.1, y_s_port - 0.15, 'BS', ha='center', va='top')
od.photodiode(x_spin_pd, y_spin_pd, -180)
od.annotation(x_spin_pd + 0.05, y_spin_pd - 0.15, 'Spin\nPD', ha='center', va='top')
od.flip_mirror(x_aperture - 0.03 + 0.2, y_spin_pd, -45, False, False, True)
od.annotation(x_aperture - 0.4 + 0.2, y_spin_pd - 0.15, 'Flip-\nmounted\ndichroic\nmirror', ha='right', va='bottom')
od.camera(x_aperture + 0.2, y_top_cam, -90)
od.annotation(x_aperture + 0.2, y_top_cam + 0.2, 'Top camera', ha='center', va='bottom')
od.led(x_aperture - 0.1, y_s_port + 0.3, -90, color='darkred')
od.annotation(x_aperture - 0.25, y_s_port + 0.35, '880 nm LED', ha='right', va='bottom')
od.mirror(x_aperture + 0.22, y_s_port - 0.02, 135)

# SIDE CAMERAS
od.camera(x_sphere, y_top_cam, -90)
od.cube_bs(x_sphere, y_spin_pd)
od.annotation(x_sphere - 0.1, y_spin_pd + 0.1, 'BS', ha='right', va='bottom')
od.camera(x_lens_2, y_top_cam, -90)
od.annotation((x_sphere + x_lens_2)/2., y_top_cam + 0.2, 'Side cameras', ha='center', va='bottom')
od.beamsplitter(x_lens_2, y_spin_pd, 45)
od.annotation(x_lens_2 - 0.1, y_spin_pd + 0.1, 'BS', ha='right', va='bottom')
od.led(x_piezo, y_spin_pd, 0, color='darkred')
od.annotation(x_piezo, y_spin_pd + 0.15, '880 nm LED', ha='center', va='bottom')
od.beam_dump(x_lens_2, y_spin_pd - 0.15, 90)
od.laser_beam(((x_sphere, y_sphere), (x_sphere, y_spin_pd), (x_lens_2, y_spin_pd), \
               (x_lens_2, y_top_cam)), 3*beam_width, color='darkred', alpha=led_alpha)
od.laser_beam(((x_sphere, y_spin_pd), (x_sphere, y_top_cam)), 3*beam_width, \
              color='darkred', alpha=led_alpha)
od.laser_beam(((x_piezo, y_spin_pd), (x_lens_2, y_spin_pd), (x_lens_2, y_spin_pd - 0.15)), \
              3*beam_width, color='darkred', alpha=led_alpha)

od.annotation(0.8, 3.8, 'Input optics', fontweight='bold', ha='center', va='center', fontsize=12)
od.annotation(5.2, 3.8, 'Output optics', fontweight='bold', ha='center', va='center', fontsize=12)

od.savefig(OUTDIR / 'microsphere_setup.png', dpi=300, pad_inches=0.0)
od.savefig(OUTDIR / 'microsphere_setup.pdf')
print(f"Wrote {OUTDIR / 'microsphere_setup.png'} and .pdf")
