"""The :class:`OpticsDiagram` drawing canvas.

:class:`OpticsDiagram` wraps a single matplotlib axis and exposes one method per optical
element (mirror, lens, beamsplitter, photodiode, ...). Each method draws its element
onto the canvas at a given ``(x, y)`` position and orientation and returns nothing --
you place an element where you want it and move on. Beams, wires, annotations and a few
coordinate helpers round out the API.

Everything is laid out in *data coordinates*: positions, the per-element
``component_size`` and beam paths are all expressed in the same units as the axis
limits, so a layout is just arithmetic on a shared coordinate grid. Linewidths and
marker sizes that need to track the data scale are converted on the fly via
:meth:`OpticsDiagram.data_to_points`.

The visual style -- soft gradients on glass elements, gold electrodes, evergreen
quadrant detectors and so on -- was inspired by the gwoptics Component Library
(http://www.gwoptics.org/ComponentLibrary/).
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import (
    Wedge, PathPatch, Rectangle, Circle, Polygon, FancyBboxPatch,
)
from matplotlib.path import Path
from matplotlib.transforms import Affine2D
from matplotlib import markers
from matplotlib.colors import to_rgba, to_rgb

from .registry import COMPONENT_REGISTRY, component


class OpticsDiagram:
    """A matplotlib canvas for drawing publication-quality optics layouts.

    The canvas owns a single matplotlib :class:`~matplotlib.axes.Axes` with equal aspect
    and no ticks or (by default) frame. Optical elements are added by calling the
    corresponding method, e.g. ``od.mirror(1.0, 2.0, angle=45)``. All coordinates,
    sizes and beam paths are in data units shared with the axis limits.

    Parameters
    ----------
    figsize : tuple of float, optional
        ``(width, height)`` of the figure in inches. When ``ax`` is not supplied this
        also sets the data limits to ``[0, width] x [0, height]`` so that one data unit
        equals one inch and the layout is easy to reason about. Required unless ``ax``
        is given.
    component_size : float, optional
        Reference length (in data units) that sets the nominal scale of every element.
        Individual elements are sized as fixed multiples of this value. Defaults to
        ``0.22``.
    fontsize : float, optional
        Font size for annotations and labels. Defaults to ``component_size * 50``.
    colors : list of color, optional
        Reserved colour cycle. Defaults to matplotlib's default property cycle. The
        built-in elements use their own dedicated palettes (see the ``*_colors``
        attributes set in ``__init__``); override those attributes after construction
        to restyle elements.
    check_frame : bool, optional
        If ``True`` the axis frame (spines) is drawn -- useful while positioning
        elements. Defaults to ``False``.
    ax : matplotlib.axes.Axes, optional
        Draw into an existing axis instead of creating a new figure. When given, the
        axis is configured (equal aspect, ticks removed) and, if ``figsize`` is also
        supplied, its limits are set to ``[0, figsize[0]] x [0, figsize[1]]``. This is
        used to tile many canvases into one figure (e.g. the component gallery) and to
        embed a diagram inside a larger subplot grid.

    Attributes
    ----------
    fig : matplotlib.figure.Figure
        The figure being drawn on.
    ax : matplotlib.axes.Axes
        The axis being drawn on.
    component_size : float
        The reference element size described above.
    lw : float
        Base linewidth used throughout, scaled from ``component_size``.
    """

    def __init__(self, figsize=None, component_size=0.22, fontsize=None, colors=None,
                 check_frame=False, ax=None):

        if ax is None:
            if figsize is None:
                raise ValueError("Provide either `figsize` or an existing `ax`.")
            fig, ax = plt.subplots(figsize=figsize, layout='constrained')
        else:
            fig = ax.figure

        ax.set_frame_on(check_frame)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_aspect('equal')
        if figsize is not None:
            ax.set_xlim([0, figsize[0]])
            ax.set_ylim([0, figsize[1]])

        self.component_size = component_size
        if colors is None:
            colors = plt.rcParamsDefault['axes.prop_cycle'].by_key()['color']
        if fontsize is None:
            self.fontsize = self.component_size*50
        else:
            self.fontsize = fontsize

        self.ax = ax
        self.fig = fig
        self.lw = self.component_size*1.5
        self.laser_color = 'red'
        self.laser_alpha = 0.4
        self.glass_colors = ['lightcyan', 'cyan', 'silver']
        self.glass_alpha = 0.7
        self.collimator_colors = ['white', 'gray']
        self.photodiode_colors = [self.blend_with_white('darkorchid'), 'darkorchid']
        self.electrode_colors = ['goldenrod', 'gold']
        self.piezo_color = 'saddlebrown'
        self.hwp_colors = [self.blend_with_white('darkorange'), 'darkorange']
        self.qwp_colors = [self.blend_with_white('orchid'), 'orchid']
        self.microsphere_color = ['white', 'lightsteelblue']
        self.camera_colors = ['silver', 'black']
        self.qpd_color = 'xkcd:evergreen'
        self.parabolic_colors = [self.blend_with_white('dodgerblue'), 'dodgerblue']
        self.faraday_colors = [self.blend_with_white('green'), 'green']
        self.beamdump_colors = ['black', 'gray']
        self.fiber_color = 'black'
        self.mirror_colors = ['white', 'silver']
        self.polarizer_colors = [self.blend_with_white('seagreen'), 'seagreen']
        self.chamber_color = 'grey'
        self.dichroic_colors = [self.blend_with_white('mediumslateblue'), 'mediumslateblue']
        self.eom_colors = ['xkcd:pale brown', 'lemonchiffon']  # [electrodes, crystal]
        self.circulator_color = 'xkcd:very light green'
        self.coupler_color = 'xkcd:pale gold'
        self.filament_color = 'xkcd:orangey red'
        self.needle_colors = ['darkgrey', 'xkcd:electric lime']  # [shaft, glowing tip]

    @staticmethod
    def list_components():
        """Return the registry of placeable components.

        Returns
        -------
        dict
            Mapping of registry key to metadata (``method``, ``display_name``,
            ``category``, ``demo``) for every element decorated with
            :func:`opticsdiagram.registry.component`. The gallery script and any code
            that wants to enumerate available elements reads from this.
        """
        return COMPONENT_REGISTRY

    def blend_with_white(self, color, fraction=0.5):
        """Return ``color`` linearly blended toward white.

        Used to build the lighter end of the two-tone gradients that give glass and
        other elements their soft shading.

        Parameters
        ----------
        color : color
            Any matplotlib colour specification.
        fraction : float, optional
            Blend fraction in ``[0, 1]``; ``0`` returns ``color`` unchanged, ``1``
            returns white. Defaults to ``0.5``.

        Returns
        -------
        tuple of float
            The blended RGB colour.
        """
        base = np.array(to_rgb(color))
        white = np.array([1, 1, 1])
        return tuple((1 - fraction) * base + fraction * white)

    def savefig(self, path, **kwargs):
        """Save the figure to ``path``.

        Thin wrapper around :meth:`matplotlib.figure.Figure.savefig`; extra keyword
        arguments (``dpi``, ``bbox_inches``, ...) are forwarded unchanged.
        ``pad_inches`` defaults to ``0`` (pass it explicitly to override).

        Parameters
        ----------
        path : str or path-like
            Output file path; the format is inferred from the extension.
        **kwargs
            Forwarded to :meth:`~matplotlib.figure.Figure.savefig`.
        """
        kwargs.setdefault('pad_inches', 0.)
        self.fig.savefig(path, **kwargs)

    @component("Beamsplitter cube", "Beamsplitters")
    def cube_bs(self, x, y, angle=0, block_beam=False, dichroic=False):
        """Draw a cube beamsplitter centred at ``(x, y)``.

        A square glass cube with its diagonal splitting surface drawn as a line. Used
        for (polarizing) beamsplitter cubes.

        Parameters
        ----------
        x, y : float
            Centre of the cube.
        angle : float, optional
            Rotation in degrees. Defaults to ``0``.
        block_beam : bool, optional
            If ``True``, fill one triangular half opaque white so a beam drawn beneath
            the cube appears to terminate inside it. Defaults to ``False``.
        dichroic : bool, optional
            If ``True``, use the dichroic (slate-blue) palette instead of the glass
            palette. Defaults to ``False``.
        """
        width = self.component_size
        colors = self.glass_colors[:2]
        if dichroic:
            colors = self.dichroic_colors
        points = ((x - width/2, y - width/2), \
                  (x - width/2, y + width/2), \
                  (x + width/2, y - width/2), \
                  (x + width/2, y + width/2))
        rotated = self.rotate(points, angle, (x, y))
        if block_beam:
            white = Polygon(rotated[1:], fc='white', ec='none', zorder=10)
            self.ax.add_patch(white)
        patch = Rectangle((x - width/2, y - width/2), width, width,
                          angle=angle, rotation_point='center', ec=self.glass_colors[2], \
                          fc='none', lw=self.lw, zorder=100)
        self.apply_gradient(patch, *colors, angle=angle + 45, alpha=self.glass_alpha)
        self.ax.plot(rotated[1:3, 0], rotated[1:3, 1], color=self.glass_colors[2], \
                     lw=self.lw, solid_capstyle='butt', zorder=100)
        self.ax.add_patch(patch)

    @component("Pellicle beamsplitter", "Beamsplitters")
    def pellicle(self, x, y, angle=0):
        """Draw a pellicle beamsplitter: a thin, nearly transparent film.

        Parameters
        ----------
        x, y : float
            Centre of the pellicle.
        angle : float, optional
            Rotation in degrees. Defaults to ``0`` (film along the vertical axis).
        """
        self._film(x, y, angle, self.glass_colors[2], alpha=0.7)

    @component("Polarizer", "Polarization")
    def polarizer(self, x, y, angle=0):
        """Draw a polarizer as an upright plate in the polarizer (sea-green) palette.

        Parameters
        ----------
        x, y : float
            Centre of the polarizer.
        angle : float, optional
            Rotation in degrees. Defaults to ``0``.
        """
        self._plate(x, y, angle, self.polarizer_colors)

    def _film(self, x, y, angle, color, alpha):
        """Draw a thin film (a line plus small mount markers) -- the pellicle primitive.

        Internal helper shared by film-like elements.

        Parameters
        ----------
        x, y : float
            Centre of the film.
        angle : float
            Rotation in degrees.
        color : color
            Line colour of the film.
        alpha : float
            Opacity of the film line.
        """
        width = self.component_size
        size = 0.1*width
        size_pts = self.data_to_points(size)
        points = ((x, y - width/2 + size/2), (x, y + width/2 - size/2))
        rotated = self.rotate(points, angle, (x, y))
        self.ax.plot(rotated[:, 0], rotated[:, 1], lw=4*self.lw, marker='none', \
                     color=color, alpha=alpha)
        self.ax.plot(rotated[:, 0], rotated[:, 1], ls='none', marker=(4, 0, angle + 45), \
                     ms=size_pts, color='k')

    @component("Mirror", "Mirrors")
    def mirror(self, x, y, angle=0, alpha=1):
        """Draw a flat mirror: a thin reflective slab with a bright front face.

        Parameters
        ----------
        x, y : float
            Centre of the mirror.
        angle : float, optional
            Rotation in degrees; the reflective face points along ``+x`` at
            ``angle = 0``. Defaults to ``0``.
        alpha : float, optional
            Opacity, used to draw faded/ghosted mirrors (e.g. the back of a flip
            mirror). Defaults to ``1``.
        """
        width = 0.2*self.component_size
        height = self.component_size
        patch = Rectangle((x - width/2, y - height/2), width, height, \
                          fc='none', ec=self.blend_with_white('k', 1 - alpha), lw=2*self.lw, \
                          angle=angle, rotation_point=(x, y), zorder=100)
        self.apply_gradient(patch, *self.mirror_colors, 'linear', angle=angle, alpha=alpha)
        self.ax.add_patch(patch)
        points = ((x + width/2, y - height/2), (x + width/2, y + height/2))
        points = self.rotate(points, angle, (x, y))
        self.ax.plot(points[:,0], points[:,1], lw=2*self.lw, \
                     color=self.blend_with_white(self.glass_colors[2], 1 - alpha), \
                     zorder=1000)

    @component("Prism mirror", "Mirrors")
    def prism_mirror(self, x, y, angle=0, block_beam=True):
        """Draw a right-angle prism mirror (a triangular glass prism).

        Parameters
        ----------
        x, y : float
            Centre of the bounding square the triangle is cut from.
        angle : float, optional
            Rotation in degrees. Defaults to ``0``.
        block_beam : bool, optional
            If ``True``, mask the hypotenuse side opaque white so an incoming beam
            appears to reflect off the prism face. Defaults to ``True``.
        """
        width = self.component_size
        points = ((x - width/2, y - width/2), \
                  (x - width/2, y + width/2), \
                  (x + width/2, y - width/2), \
                  (x + width/2, y + width/2))
        rotated = self.rotate(points, angle, (x, y))
        patch = Polygon(rotated[:3], fc='none', ec=self.glass_colors[2], lw=self.lw, zorder=100)
        self.apply_gradient(patch, *self.glass_colors[:2], angle=angle + 45, alpha=self.glass_alpha)
        self.ax.add_patch(patch)
        if block_beam:
            white = Polygon(rotated[1:], fc='white', ec='white', lw=2*self.lw, zorder=1000)
            self.ax.add_patch(white)
        self.ax.plot(rotated[1:3, 0], rotated[1:3, 1], color=self.glass_colors[2], \
                     lw=2*self.lw, zorder=1000)

    @component("Flip mirror", "Mirrors")
    def flip_mirror(self, x, y, angle=0, reflected=False, block_beam=True, dichroic=False):
        """Draw a flip-mounted mirror: a mirror on a hinged mount with its raised ghost.

        Renders the mirror in the beam path together with a faded copy folded up on its
        hinge, plus the mount arm and pivot, to convey that the optic can be flipped in
        and out.

        Parameters
        ----------
        x, y : float
            Centre of the in-beam mirror.
        angle : float, optional
            Rotation in degrees. Defaults to ``0``.
        reflected : bool, optional
            Mirror the mount geometry left-to-right (hinge on the other side).
            Defaults to ``False``.
        block_beam : bool, optional
            If ``True``, mask behind the mirror so a beam appears to terminate on it.
            Defaults to ``True``.
        dichroic : bool, optional
            If ``True``, draw the optic as a dichroic plate (partially transmissive)
            rather than a solid mirror. Defaults to ``False``.
        """
        axle_offset = 0.2*self.component_size
        mount_thickness = 0.1*self.component_size
        mount_lw = self.data_to_points(mount_thickness)
        height = self.component_size
        width = 0.2*self.component_size
        axle_rad = 0.1*self.component_size
        mount_frac = 0.5
        if dichroic:
            mount_frac = 0.15
        mirror_alpha = 0.3
        points = ((x - 0.5*height - 0.5*width - 0.5*mount_thickness - axle_offset, \
                   y - 0.5*height + 0.5*width - axle_offset + 0.5*mount_thickness), \
                  (x - 0.5*width - 0.5*mount_thickness, y - (0.5 - mount_frac)*height), \
                  (x - 0.5*width - 0.5*mount_thickness, y - 0.5*height - axle_offset), \
                  (x - 0.5*width - 0.5*mount_thickness - mount_frac*height - axle_offset, \
                   y - 0.5*height - axle_offset))

        if reflected:
            xy_arr = np.array([[x, y] for i in range(4)])
            points = (np.array(points) - xy_arr)*np.array((-1, 1))[None, :] + xy_arr

        rot = self.rotate(points, angle, (x, y))
        if block_beam:
            white = Rectangle((x - 2*width, y - height/2), 2*width, height, fc='white', \
                              ec='white', angle=angle + 180*int(reflected), \
                              rotation_point=(x, y), zorder=10)
            self.ax.add_patch(white)
        if dichroic:
            self._plate(*rot[0], angle + 90, colors=self.dichroic_colors, alpha=mirror_alpha)
            self._plate(x, y, angle + 180*int(reflected), colors=self.dichroic_colors)
        else:
            self.mirror(*rot[0], angle + 90, mirror_alpha)
            self.mirror(x, y, angle + 180*int(reflected))
        self.ax.plot(rot[2:,0], rot[2:,1], lw=mount_lw, \
                     color=self.blend_with_white('k', 1 - mirror_alpha), zorder=1000)
        self.ax.plot(rot[1:3,0], rot[1:3,1], lw=mount_lw, color='k', zorder=1000)
        axle = Circle(rot[2], axle_rad, \
                      ec='k', fc=self.piezo_color, lw=self.lw, zorder=1000)
        self.ax.add_patch(axle)

    @component("Piezo deflector", "Mirrors")
    def piezo_deflector(self, x, y, angle=0, reflected=False):
        """Draw a piezo-actuated steering mirror with motion-blur ghosts.

        A mirror on a pivot, drawn with a few fading offset copies to suggest the small
        angular dither imparted by a piezo actuator.

        Parameters
        ----------
        x, y : float
            Centre of the mirror.
        angle : float, optional
            Rotation in degrees. Defaults to ``0``.
        reflected : bool, optional
            Flip the pivot to the opposite corner and reverse the dither direction.
            Defaults to ``False``.
        """
        width = 0.2*self.component_size
        height = self.component_size
        offset = np.sqrt(height**2/4. + width**2/4.)
        rot = 5.
        num_shadows = 3
        axle_rad = 0.5*width

        if reflected:
            rot *= -1

        for i in range(num_shadows):
            shadow = Rectangle((x - width/2 - offset*np.sin(np.deg2rad((1 + i)*rot)), \
                                y - height/2 + offset*(1 - np.cos(np.deg2rad((1 + i)*rot)))), \
                               width, height, fc='none', ec='k', lw=2*self.lw, \
                               angle=angle + (1 + i)*rot, rotation_point=(x, y), \
                               zorder=10, alpha=0.3*(1 - i/num_shadows))
            self.apply_gradient(shadow, *self.mirror_colors, 'linear', angle=angle + (1 + i)*rot, \
                                alpha=0.3*(1 - i/num_shadows))
            self.ax.add_patch(shadow)

        self.mirror(x, y, angle + 180*int(reflected))

        axle_points = ((x, y), (x - np.sign(rot)*(width/2 + axle_rad), y - height/2 + axle_rad))
        axle_points = self.rotate(axle_points, angle, (x, y))

        axle = Circle(axle_points[1], axle_rad, \
                      ec='k', fc=self.piezo_color, lw=self.lw, zorder=1000)
        self.ax.add_patch(axle)

    @component("Half-wave plate", "Polarization")
    @component("Quarter-wave plate", "Polarization", demo={"quarter": True}, key="qwp")
    def waveplate(self, x, y, angle=0, quarter=False):
        """Draw a wave plate as an upright plate in the half- or quarter-wave palette.

        Parameters
        ----------
        x, y : float
            Centre of the wave plate.
        angle : float, optional
            Rotation in degrees. Defaults to ``0``.
        quarter : bool, optional
            If ``True`` use the quarter-wave (orchid) palette; otherwise the half-wave
            (orange) palette. Defaults to ``False``.
        """
        colors = self.hwp_colors
        if quarter:
            colors = self.qwp_colors
        self._plate(x, y, angle, colors)

    @component("Plate beamsplitter", "Beamsplitters")
    def beamsplitter(self, x, y, angle=0):
        """Draw a plate beamsplitter as an upright glass plate.

        Parameters
        ----------
        x, y : float
            Centre of the plate.
        angle : float, optional
            Rotation in degrees. Defaults to ``0``.
        """
        colors = self.glass_colors[:2]
        self._plate(x, y, angle, colors)

    def _plate(self, x, y, angle, colors, alpha=1., hatch=None):
        """Draw a thin rectangular plate -- the primitive for plate-like optics.

        Internal helper shared by wave plates, plate beamsplitters, polarizers and the
        diffuser.

        Parameters
        ----------
        x, y : float
            Centre of the plate.
        angle : float
            Rotation in degrees.
        colors : sequence of color
            Two colours defining the reflected gradient across the plate.
        alpha : float, optional
            Opacity multiplier applied on top of the glass alpha. Defaults to ``1``.
        hatch : str, optional
            Matplotlib hatch pattern (used to texture the diffuser). Defaults to
            ``None``.
        """
        width = 0.2*self.component_size
        height = self.component_size
        with plt.rc_context({'hatch.linewidth': 0, 'hatch.color': 'dimgray'}):
            patch = Rectangle((x - width/2, y - height/2), width, height, \
                              fc='none', ec=self.glass_colors[2], lw=self.lw, angle=angle, \
                              rotation_point=(x, y), zorder=100, hatch=hatch)
        self.apply_gradient(patch, *colors, 'reflected', alpha=self.glass_alpha*alpha, \
                            angle=angle + 90)
        self.ax.add_patch(patch)

    @component("Optical fiber", "Fibers & couplers")
    def fiber(self, x, y, angle=0, reflected=False):
        """Draw a coiled optical fiber terminating at ``(x, y)``.

        Typically attached to the back of a :meth:`collimator`. The coil is drawn with a
        short lead-in and a lead-out that ends at ``(x, y)``.

        Parameters
        ----------
        x, y : float
            Position of the fiber's terminating end.
        angle : float, optional
            Orientation in degrees. Defaults to ``0``.
        reflected : bool, optional
            Mirror the coil handedness. Defaults to ``False``.
        """
        n_turns = 3
        points_per_turn = 300
        radius = 0.2*self.component_size
        dx_per_turn = radius / 2
        ext_start = self.component_size*0.3
        ext_end = self.component_size*0.4
        refl_fac = 1 - 2*int(reflected)

        n_points = int((n_turns + 0.25) * points_per_turn)
        theta = np.linspace(0, 2 * np.pi * (n_turns + 0.25), n_points)
        xp = radius * refl_fac*np.sin(theta) + refl_fac*dx_per_turn*theta/(2*np.pi)
        yp = radius * np.cos(theta)
        x_all = np.concatenate([[xp[0] - refl_fac*ext_start], \
                                [xp[0]], xp, [xp[-1], xp[-1]]])
        y_all = np.concatenate([[yp[0]], [yp[0]], yp, [yp[-1], yp[-1] - ext_end]])
        angle_rad = np.deg2rad(angle + 90)
        x_rot = x_all * np.cos(angle_rad) - y_all * np.sin(angle_rad)
        y_rot = x_all * np.sin(angle_rad) + y_all * np.cos(angle_rad)
        dx = x - x_rot[-1]
        dy = y - y_rot[-1]
        x_final = x_rot + dx
        y_final = y_rot + dy

        self.ax.plot(x_final, y_final, color=self.fiber_color, lw=1.5*self.lw)

    @component("Fiber collimator", "Fibers & couplers", demo={"fiber": True})
    def collimator(self, x, y, angle=0, fiber=False, reflected=False):
        """Draw a fiber collimator: a tapered barrel with an optional fiber pigtail.

        Parameters
        ----------
        x, y : float
            Position of the collimator's output face (where the beam emerges).
        angle : float, optional
            Orientation in degrees; the beam exits along ``+x`` at ``angle = 0``.
            Defaults to ``0``.
        fiber : bool, optional
            If ``True``, draw a coiled :meth:`fiber` attached to the back. Defaults to
            ``False``.
        reflected : bool, optional
            Handedness of the attached fiber coil. Defaults to ``False``.
        """
        width = 0.75*self.component_size
        height = self.component_size/2.
        ext_width = 0.25*self.component_size
        ext_height_1 = 0.1*self.component_size
        ext_height_2 = 0.4*self.component_size

        rect = Rectangle((x - width, y - height/2), width, height, \
                          fc='none', ec='k', lw=self.lw, angle=angle, \
                          rotation_point=(x, y), zorder=100)

        ext_points = ((x - width - ext_width, y - ext_height_1/2), \
                      (x - width - ext_width, y + ext_height_1/2), \
                      (x - width, y + ext_height_2/2), \
                      (x - width, y - ext_height_2/2))

        rotated_points = self.rotate(ext_points, angle, (x, y))

        poly = Polygon(rotated_points, fc='k', zorder=100)
        self.ax.add_patch(poly)

        self.apply_gradient(rect, *self.collimator_colors, 'reflected', angle=angle + 90)
        self.ax.add_patch(rect)

        if fiber:
            self.fiber(np.mean(rotated_points[:2, 0]), \
                       np.mean(rotated_points[:2, 1]), angle, reflected)

    @component("Photodiode", "Detectors")
    def photodiode(self, x, y, angle=0):
        """Draw a photodiode: a half-disc active area on a flat surface, with a lead.

        Parameters
        ----------
        x, y : float
            Centre of the photodiode's front surface.
        angle : float, optional
            Orientation in degrees; at ``angle = 0`` the active face looks toward
            ``-x``, catching a rightward beam. Defaults to ``0``.
        """
        angle = angle + 90  # reorient so the default active face catches a rightward beam
        radius = self.component_size/2.
        diode_size = 0.5*radius
        diode_pad = 0.4*radius
        wire_thickness = 0.08*radius
        surface_thickness = 0.2*radius

        surf = Rectangle((x - radius, y), 2*radius, surface_thickness, angle=angle, \
                         rotation_point=(x, y), fc='k', ec='k', lw=self.lw, zorder=100)
        self.ax.add_patch(surf)

        patch = Wedge((x - surface_thickness*np.sin(np.deg2rad(angle)), \
                       y + surface_thickness*np.cos(np.deg2rad(angle))), \
                      radius, angle, 180 + angle, \
                      fc='none', ec='k', lw=self.lw, zorder=100)
        self.apply_gradient(patch, *self.photodiode_colors, angle=angle + 90)
        self.ax.add_patch(patch)

        tri_points = ((x - diode_size/2., y + diode_size/2 + diode_pad), \
                      (x + diode_size/2., y + diode_size + diode_pad), \
                      (x + diode_size/2., y + diode_pad))
        tri_points = self.rotate(tri_points, angle=angle, rotation_point=(x, y))

        cap = Rectangle((x - diode_size/2. - wire_thickness/2., y + diode_pad), \
                        wire_thickness, diode_size, angle=angle, rotation_point=(x, y), \
                        fc='k', ec='none', zorder=1000)
        self.ax.add_patch(cap)

        triangle = Polygon(tri_points, fc='k', ec='none', zorder=1000)
        self.ax.add_patch(triangle)

        wire = Rectangle((x - 0.7*radius, y + diode_size/2. + diode_pad - wire_thickness/2.), \
                         1.4*radius, wire_thickness, angle=angle, rotation_point=(x, y), \
                         fc='k', ec='none', zorder=1000)
        self.ax.add_patch(wire)

    @component("Quadrant photodiode", "Detectors")
    def qpd(self, x, y, angle=0):
        """Draw a quadrant photodiode: a photodiode plus a quartered sensing area.

        Builds on :meth:`photodiode`, adding the square four-quadrant sensor (split by
        a cross) and a dashed enclosure.

        Parameters
        ----------
        x, y : float
            Centre of the photodiode's front surface (the quadrant area sits beyond it).
        angle : float, optional
            Orientation in degrees; at ``angle = 0`` the sensor catches a rightward
            beam. Defaults to ``0``.
        """
        radius = self.component_size/2.
        wire_thickness = 0.08*radius
        surface_size = 2*radius
        surface_thickness = 0.2*radius

        self.photodiode(x, y, angle)

        # the photodiode applies its own reorientation; match the quadrant stack to it
        angle = angle + 90

        surf = Rectangle((x - radius, y + radius + 2*surface_thickness), \
                         2*radius, surface_size, angle=angle, rotation_point=(x, y), \
                         fc=self.qpd_color, ec='k', lw=self.lw, zorder=100)
        self.ax.add_patch(surf)

        frame = Rectangle((x - radius, y), 2*radius, surface_size + radius + 2*surface_thickness, \
                          angle=angle, rotation_point=(x, y), \
                          fc='none', ec='k', lw=self.lw, ls='--', zorder=100)
        self.ax.add_patch(frame)

        vert = Rectangle((x - wire_thickness/2, y + radius + 2*surface_thickness), \
                         wire_thickness, surface_size, angle=angle, \
                         rotation_point=(x, y), ec='none', fc='white', zorder=1000)
        self.ax.add_patch(vert)

        hori = Rectangle((x - surface_size/2, \
                          y + radius + 2*surface_thickness + surface_size/2 - wire_thickness/2), \
                         surface_size, wire_thickness, angle=angle, \
                         rotation_point=(x, y), ec='none', fc='white', zorder=1000)
        self.ax.add_patch(hori)

    @component("Aperture", "Beam control")
    def aperture(self, x, y, angle=0):
        """Draw an aperture/iris as two opaque jaws with a gap between them.

        Parameters
        ----------
        x, y : float
            Centre of the aperture opening.
        angle : float, optional
            Orientation in degrees. Defaults to ``0``.
        """
        width = 0.1*self.component_size
        height = self.component_size
        gap = 0.08*self.component_size
        upper = Rectangle((x - width/2, y + gap/2), width, height/2 - gap/2, \
                          fc='k', ec='none', angle=angle, rotation_point=(x, y), zorder=100)
        lower = Rectangle((x - width/2, y - height/2), width, height/2 - gap/2, \
                          fc='k', ec='none', angle=angle, rotation_point=(x, y), zorder=100)
        self.ax.add_patch(upper)
        self.ax.add_patch(lower)

    @component("Lens", "Lenses")
    def lens(self, x, y, angle=0):
        """Draw a biconvex lens centred at ``(x, y)``.

        Parameters
        ----------
        x, y : float
            Centre of the lens.
        angle : float, optional
            Orientation in degrees; at ``angle = 0`` the optical axis is horizontal (a
            rightward beam passes straight through). Defaults to ``0``.
        """
        angle = angle + 90  # reorient so the default optical axis is horizontal
        width = self.component_size
        thickness = 0.3*width
        radius = 1.5*width
        half_width = width / 2
        resolution = 50

        xvals = np.linspace(-half_width, half_width, resolution)
        y_upper = y + np.sqrt(np.clip(radius**2 - xvals**2, 0, None)) - radius + thickness/2
        y_lower = y - np.sqrt(np.clip(radius**2 - xvals**2, 0, None)) + radius - thickness/2

        verts = np.column_stack((xvals + x, y_upper))
        verts = np.vstack((verts, np.column_stack((xvals[::-1] + x, y_lower[::-1]))))
        verts = np.vstack((verts, verts[0]))

        codes = [Path.MOVETO] + [Path.LINETO] * (2 * resolution - 1) + [Path.CLOSEPOLY]
        transform = Affine2D().rotate_deg_around(x, y, angle) + self.ax.transData

        patch = PathPatch(Path(verts, codes), transform=transform, lw=self.lw, \
                          ec=self.glass_colors[2], fc='none', zorder=100)
        self.apply_gradient(patch, *self.glass_colors[:2], 'reflected', alpha=self.glass_alpha)
        self.ax.add_patch(patch)

    @component("Lens holder", "Lenses")
    def lens_holder(self, x, y, angle=0):
        """Draw a pair of mounting blocks flanking a :meth:`lens`.

        Place at the same ``(x, y, angle)`` as a lens to suggest its mount.

        Parameters
        ----------
        x, y : float
            Centre of the lens being held.
        angle : float, optional
            Orientation in degrees, matching the lens (``angle = 0`` for a horizontal
            optical axis). Defaults to ``0``.
        """
        angle = angle + 90  # reorient to match the lens default (horizontal axis)
        width = self.component_size
        thickness = 0.3 * width
        left = Rectangle((x - width / 2 - thickness, y - thickness / 2), thickness, thickness, fc='silver', ec='none', angle=angle, rotation_point=(x, y))
        right = Rectangle((x + width / 2, y - thickness / 2), thickness, thickness, angle=angle, fc='silver', ec='none', rotation_point=(x, y))
        self.ax.add_patch(left)
        self.ax.add_patch(right)

    @component("Faraday rotator", "Polarization")
    def faraday_rotator(self, x, y, angle=0):
        """Draw a Faraday rotator/isolator as a wide green-shaded block.

        Parameters
        ----------
        x, y : float
            Centre of the rotator.
        angle : float, optional
            Orientation in degrees. Defaults to ``0``.
        """
        width = 2*self.component_size
        height = self.component_size
        patch = Rectangle((x - width/2, y - height/2), width, height, angle=angle, \
                          rotation_point=(x, y), fc='none', ec='k', lw=self.lw, zorder=100)
        self.apply_gradient(patch, *self.faraday_colors, mode='reflected', angle=angle + 90)
        self.ax.add_patch(patch)

    @component("Parabolic mirror", "Mirrors")
    def parabolic_mirror(self, x, y, angle=0, reflected=False):
        """Draw an off-axis parabolic mirror with a curved reflective face.

        Parameters
        ----------
        x, y : float
            Reference position of the mirror.
        angle : float, optional
            Orientation in degrees; at ``angle = 0`` the mirror takes in a rightward
            beam. Defaults to ``0``.
        reflected : bool, optional
            Flip the parabola so the tall side is on the opposite end. Defaults to
            ``False``.
        """
        angle = angle - 90  # reorient so the default beam axis is horizontal
        width = 1.4*self.component_size
        height = 2*self.component_size
        offset = 0.2*height
        bl = (0, 0)
        tl = (0, [offset, height][int(reflected)])
        tr = (width,[height, offset][int(reflected)])
        br = (width, 0)
        resolution = 50

        transform = Affine2D().rotate_deg_around(x, y, angle) + self.ax.transData

        x_parab = np.linspace(tl[0], tr[0], resolution)
        x0 = [tl[0], tr[0]][int(reflected)]
        a = (height - offset) / (width - 0.01*offset)**2

        y_parab = a * (x_parab - x0)**2 + offset

        verts = np.array([bl, tl] + list(zip(x_parab, y_parab)) + [tr, tr, br, bl])
        verts += np.array((x - 0.35*width, y - 0.35*height))
        codes = [Path.MOVETO] + \
                [Path.LINETO] * (2 + resolution) + \
                [Path.LINETO] * 2 + \
                [Path.CLOSEPOLY]

        patch = PathPatch(Path(verts, codes), transform=transform, lw=self.lw, \
                          fc='none', ec='k', zorder=1000)
        self.apply_gradient(patch, *self.parabolic_colors, mode='reflected')
        self.ax.add_patch(patch)

    @component("Microsphere", "Chambers & traps", demo={"radius": 0.15})
    def microsphere(self, x, y, radius=None):
        """Draw a levitated microsphere as a radially-shaded sphere.

        Parameters
        ----------
        x, y : float
            Centre of the sphere.
        radius : float, optional
            Sphere radius in data units. Defaults to ``0.1 * component_size``.
        """
        if radius is None:
            radius = 0.1*self.component_size
        circ = Circle((x, y), radius, fc='none', ec='none')
        self.apply_gradient(circ, *self.microsphere_color, 'radial')
        self.ax.add_patch(circ)

    @component("Camera", "Detectors")
    def camera(self, x, y, angle=0):
        """Draw a camera: a body with a protruding lens barrel.

        Parameters
        ----------
        x, y : float
            Reference position at the front of the lens.
        angle : float, optional
            Orientation in degrees; at ``angle = 0`` the lens looks toward ``-x``,
            imaging a rightward beam. Defaults to ``0``.
        """
        angle = angle - 90  # reorient so the default lens faces a rightward beam
        width = 1.1*self.component_size
        height = 0.3*width
        lens_length = 0.3*width
        lens_width = 0.7*width
        body = Rectangle((x - width/2, y - lens_length - height), width, height, \
                         angle=angle, rotation_point=(x, y), fc='none', ec='k', zorder=1000, \
                         lw=self.lw)
        self.apply_gradient(body, *self.camera_colors, 'reflected', angle=angle)
        self.ax.add_patch(body)
        body = Rectangle((x - lens_width/2, y - lens_length), lens_width, lens_length, \
                         angle=angle, rotation_point=(x, y), fc='none', ec='k', zorder=1000, \
                         lw=self.lw)
        self.apply_gradient(body, *self.camera_colors, 'reflected', angle=angle)
        self.ax.add_patch(body)

    @component("Electrode cube", "Chambers & traps")
    def electrode_cube(self, x, y, angle=0):
        """Draw four trapezoidal electrodes arranged around a central point.

        Represents the electrode assembly surrounding a trapped microsphere.

        Parameters
        ----------
        x, y : float
            Centre of the electrode assembly.
        angle : float, optional
            Orientation in degrees. Defaults to ``0``.
        """
        width = 2*self.component_size
        gap = 0.1*width
        thickness = 0.3*width
        left_points = ((x - width/2, y - width/2 + gap/2), \
                       (x - width/2, y + width/2 - gap/2), \
                       (x - width/2 + thickness, y + width/2 - gap/2 - thickness), \
                       (x - width/2 + thickness, y - width/2 + gap/2 + thickness))
        left_points = self.rotate(left_points, angle, (x, y))
        left = Polygon(left_points, lw=self.lw, fc='none', ec='k', zorder=100)
        self.apply_gradient(left, *self.electrode_colors, angle=angle)
        self.ax.add_patch(left)
        top_points = self.rotate(left_points, angle - 90, (x, y))
        top = Polygon(top_points, lw=self.lw, fc='none', ec='k', zorder=100)
        self.apply_gradient(top, *self.electrode_colors, angle=angle)
        self.ax.add_patch(top)
        right_points = self.rotate(left_points, angle - 180, (x, y))
        right = Polygon(right_points, lw=self.lw, fc='none', ec='k', zorder=100)
        self.apply_gradient(right, *self.electrode_colors, angle=angle)
        self.ax.add_patch(right)
        bottom_points = self.rotate(left_points, angle + 90, (x, y))
        bottom = Polygon(bottom_points, lw=self.lw, fc='none', ec='k', zorder=100)
        self.apply_gradient(bottom, *self.electrode_colors, angle=angle)
        self.ax.add_patch(bottom)

    @component("Beam dump", "Beam control")
    def beam_dump(self, x, y, angle=0):
        """Draw a beam dump: a dark finned block that absorbs an incoming beam.

        Parameters
        ----------
        x, y : float
            Position of the dump's front face.
        angle : float, optional
            Orientation in degrees; the opening faces ``-x`` at ``angle = 0``. Defaults
            to ``0``.
        """
        width = 0.4*self.component_size
        height = self.component_size
        n_fins = 8
        patch = Rectangle((x - width, y - height/2), width, height, \
                          angle=angle, rotation_point=(x, y), fc='none', ec='k', \
                          lw = self.lw, zorder=1000)
        self.apply_gradient(patch, *self.beamdump_colors, angle=angle)
        self.ax.add_patch(patch)
        points = np.vstack(((x - width)*np.ones(n_fins), \
                            np.linspace(y - height/2, y + height/2, n_fins))).T
        rotated = self.rotate(points, angle, (x, y))
        marker = markers.MarkerStyle(marker='_')
        marker._transform = marker.get_transform().rotate_deg(angle)
        self.ax.plot(rotated[:,0], rotated[:,1], color='white', \
                     ms=8*self.lw, ls='none', marker=marker, zorder=1000)

    @component("LED", "Sources", demo={"color": "darkred"})
    def led(self, x, y, angle=0, color='green'):
        """Draw an LED: a glowing emitter with a lensed package and a lead.

        Parameters
        ----------
        x, y : float
            Position of the emitting tip.
        angle : float, optional
            Orientation in degrees; at ``angle = 0`` the LED emits toward ``+x`` (a
            rightward beam). Defaults to ``0``.
        color : color, optional
            Emission colour. Defaults to ``'green'``.
        """
        angle = angle + 180  # reorient so the default emission is a rightward beam
        width = 0.6*self.component_size
        height = 0.4*self.component_size
        size = self.data_to_points(height)
        self.ax.plot(x, y, marker='x', ms=2.2*size, mew=2*self.lw, color=color)
        self.ax.plot(x, y, marker='+', ms=3.1*size, mew=2*self.lw, color=color)
        self.ax.plot(x, y, marker='o', ms=1.9*size, mew=0, color='white')
        circ = Circle((x, y), radius=height/2, fc='none', ec='none')
        self.apply_gradient(circ, self.blend_with_white(color, 0.7), color, 'linear', \
                            angle=angle, zorder=1000)
        self.ax.add_patch(circ)
        rect = Rectangle((x, y - height/2), width, height, angle=angle, rotation_point=(x, y), \
                         fc=color, ec='none', zorder=100)
        self.ax.add_patch(rect)
        cap = Rectangle((x + width, y - 1.2*height/2), 0.2*width, 1.2*height, angle=angle, \
                        rotation_point=(x, y), fc='k', ec='k', lw=2*self.lw, zorder=1000)
        self.ax.add_patch(cap)

    @component("Diffuser", "Beam control")
    def diffuser(self, x, y, angle=0):
        """Draw a diffuser as a hatched (frosted) plate.

        Parameters
        ----------
        x, y : float
            Centre of the diffuser.
        angle : float, optional
            Orientation in degrees. Defaults to ``0``.
        """
        self._plate(x, y, angle, ['white', 'lightslategray'], hatch='*'*20)

    @component("Optical circulator", "Fibers & couplers")
    def circulator(self, x, y, angle=0, reflected=False):
        """Draw an optical circulator: a circle with a curved directional arrow.

        Parameters
        ----------
        x, y : float
            Centre of the circulator.
        angle : float, optional
            Orientation in degrees. Defaults to ``0``.
        reflected : bool, optional
            Reverse the circulation direction. Defaults to ``False``.
        """
        rad = 0.6 * self.component_size
        arrow_rad = 0.6 * rad
        thickness = 0.1 * rad
        circ = Circle((x, y), rad, ec='k', lw=2 * self.lw, fc=self.circulator_color)
        self.ax.add_patch(circ)
        arrow = Wedge((x, y), arrow_rad, -60 + 60 * int(reflected) + angle, 180 + 60 * int(reflected) + angle, width=thickness, lw=0, color='k')
        self.ax.add_patch(arrow)
        head_width = 0.3 * rad
        fac = 2 * (-int(reflected) + 0.5)
        points = ((x - fac * (arrow_rad - thickness / 2) - head_width / 2, y), \
                  (x - fac * (arrow_rad - thickness / 2) + head_width / 2, y), \
                  (x - fac * (arrow_rad - thickness / 2), y - np.sqrt(3) * head_width / 2))
        points = self.rotate(points, angle, (x, y))
        head = Polygon(points, closed=True, color='k')
        self.ax.add_patch(head)

    @component("Math operation", "Diagram elements", demo={"which": "+"})
    def operation(self, x, y, which='+', angle=0):
        """Draw a circled mathematical operator (summing/difference junction).

        Parameters
        ----------
        x, y : float
            Centre of the symbol.
        which : str, optional
            Operator rendered inside the circle, e.g. ``'+'`` or ``'-'``.
            Defaults to ``'+'``.
        angle : float, optional
            Rotation of the symbol in degrees. Defaults to ``0``.
        """
        rad = 0.4 * self.component_size
        circle = Circle((x, y), rad, ec='k', fc='white', lw=2 * self.lw, zorder=100)
        self.ax.add_patch(circle)
        which = '_' if which == '-' else which
        marker = markers.MarkerStyle(which).rotated(deg=angle)
        self.ax.plot(x, y, marker=marker, ms=self.data_to_points(1.2 * rad), color='k', zorder=101)

    @component("Instrument box", "Diagram elements", demo={"label": "DAQ"})
    def instrument(self, x, y, label, width=None, height=None):
        """Draw a labelled rounded box representing an instrument (DAQ, controller, ...).

        Parameters
        ----------
        x, y : float
            Centre of the box.
        label : str
            Text shown inside the box (may contain newlines/LaTeX).
        width : float, optional
            Box width in data units. Defaults to ``1.5 * component_size``.
        height : float, optional
            Box height in data units. Defaults to ``component_size``.
        """
        if width is None:
            width = 1.5 * self.component_size
        if height is None:
            height = self.component_size
        pad = 0.2 * height
        box = FancyBboxPatch((x - (width - 2 * pad) / 2, y - (height - 2 * pad) / 2), width - 2 * pad, height - 2 * pad, \
                             boxstyle=f'round,pad={pad:.3f}', fc='white', ec='k', lw=2 * self.lw)
        self.ax.add_patch(box)
        self.ax.text(x, y, label, va='center', ha='center', fontsize=self.fontsize)

    @component("Electro-optic modulator", "Beam control")
    def eom(self, x, y, angle=0):
        """Draw an electro-optic modulator as a crystal between two electrodes.

        Parameters
        ----------
        x, y : float
            Centre of the modulator.
        angle : float, optional
            Orientation in degrees. (Currently the body is drawn upright; ``angle`` is
            accepted for call-signature consistency.) Defaults to ``0``.
        """
        width = 1.5 * self.component_size
        height = self.component_size
        upper_rect = Rectangle((x - width / 2, y + 0.3 * height), width, 0.2 * height, lw=self.lw, ec='k', fc=self.eom_colors[0])
        lower_rect = Rectangle((x - width / 2, y - 0.5 * height), width, 0.2 * height, lw=self.lw, ec='k', fc=self.eom_colors[0])
        middle_rect = Rectangle((x - width / 2, y - 0.25 * height), width, 0.5 * height, lw=self.lw, ec='k', fc=self.eom_colors[1])
        self.ax.add_patch(lower_rect)
        self.ax.add_patch(upper_rect)
        self.ax.add_patch(middle_rect)

    @component("Filament", "Electronics")
    def filament(self, x, y, angle=0):
        """Draw a heated filament (a zig-zag glowing wire on two leads).

        Parameters
        ----------
        x, y : float
            Centre of the filament.
        angle : float, optional
            Orientation in degrees. Defaults to ``0``.
        """
        height = self.component_size
        width = self.component_size / 2
        x_pts = np.array([0.4, 0.4, 0.4, 0, 0, 0.2, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.8, 1.0, 1.0, 0.6, 0.6, 0.6]) * width + x - width / 2
        y_pts = np.array([0.2, -0.2, 0, 0, 1, 1, 1.2, 0.8, 1.2, 0.8, 1.2, 0.8, 1, 1, 0, 0, 0.1, -0.1]) * height + y - height / 2
        points = self.rotate(np.array((x_pts, y_pts)).T, angle, rotation_point=(x, y))
        self.ax.plot(points[5:-5, 0], points[5:-5, 1], lw=1.5 * self.lw, color=self.filament_color)
        self.ax.plot(points[:6, 0], points[:6, 1], lw=1.5 * self.lw, color='k')
        self.ax.plot(points[-6:, 0], points[-6:, 1], lw=1.5 * self.lw, color='k')

    @component("Needle", "Electronics")
    def needle(self, x, y, angle=0):
        """Draw a needle/tip (e.g. a loading or discharge needle) with a glowing point.

        Parameters
        ----------
        x, y : float
            Position of the needle tip.
        angle : float, optional
            Orientation in degrees; the shaft extends along ``-y`` at ``angle = 0``.
            Defaults to ``0``.
        """
        height = self.component_size
        width = 0.1 * self.component_size
        points = ((x, y), (x - width / 2, y - height), (x + width / 2, y - height))
        points = self.rotate(points, angle, (x, y))
        needle = Polygon(points, ec='none', fc=self.needle_colors[0])
        self.ax.add_patch(needle)
        self.ax.plot(x, y, marker=(7, 1, 0), ms=25 * self.lw, mew=0, color=self.needle_colors[1])

    @component(
        "AC source", "Electronics",
        demo=lambda od, x, y: od.ac_source(
            x, y, [(x - 1.1 * od.component_size, y),
                   (x - 1.1 * od.component_size, y - 1.4 * od.component_size)],
        ),
    )
    def ac_source(self, x, y, wire_path, connection='left', angle=0):
        """Draw an AC source (a circled sine wave) with a wire leading away from it.

        Parameters
        ----------
        x, y : float
            Centre of the source symbol.
        wire_path : sequence of (float, float)
            Points of the wire leaving the source, starting from the chosen
            ``connection`` point on the circle.
        connection : {'left', 'right', 'top', 'bottom'}, optional
            Which side of the circle the wire attaches to. Defaults to ``'left'``.
        angle : float, optional
            Rotation of the symbol in degrees. Defaults to ``0``.
        """
        rad = 0.4 * self.component_size
        circle = Circle((x, y), rad, lw=2 * self.lw, ec='k', fc='white')
        self.ax.add_patch(circle)
        xvals = np.linspace(x - 0.6 * rad, x + 0.6 * rad, 100)
        yvals = 0.6 * rad * np.sin(2 * np.pi * (xvals - x - 0.6 * rad) / 1.2 / rad) + y
        points = self.rotate(np.array((xvals, yvals)).T, angle, rotation_point=(x, y))
        self.ax.plot(points[:, 0], points[:, 1], color='k', lw=2 * self.lw)
        cons = {'left': (x - rad, y), 'right': (x + rad, y), 'top': (x, y + rad), 'bottom': (x, y - rad)}
        point = self.rotate(np.array((cons[connection],)), angle, (x, y))
        path = np.array([point[0]] + list(wire_path)).T
        self.ax.plot(path[0], path[1], lw=2 * self.lw, color='k')

    @component(
        "Ground", "Electronics",
        demo=lambda od, x, y: od.ground(
            x + 0.4 * od.component_size, y,
            [(x + 0.4 * od.component_size, y + 1.2 * od.component_size),
             (x - 0.4 * od.component_size, y + 1.2 * od.component_size)],
        ),
    )
    def ground(self, x, y, wire_path, angle=0):
        """Draw a ground symbol with a wire leading away from it.

        Parameters
        ----------
        x, y : float
            Position of the top of the ground symbol (where the wire attaches).
        wire_path : sequence of (float, float)
            Points of the wire leaving the ground symbol.
        angle : float, optional
            Rotation of the symbol in degrees. Defaults to ``0``.
        """
        height = 0.3 * self.component_size
        width = 0.7 * self.component_size
        points = np.array(((x - width / 2, y), (x + width / 2, y), \
                           (x - 0.35 * width, y - 0.5 * height), \
                           (x + 0.35 * width, y - 0.5 * height), \
                           (x - 0.2 * width, y - height), \
                           (x + 0.2 * width, y - height)))
        points = self.rotate(points, angle, (x, y))
        self.ax.plot(points[:2, 0], points[:2, 1], lw=2 * self.lw, color='k')
        self.ax.plot(points[2:4, 0], points[2:4, 1], lw=2 * self.lw, color='k')
        self.ax.plot(points[4:, 0], points[4:, 1], lw=2 * self.lw, color='k')
        path = np.array([(x, y)] + list(wire_path)).T
        self.ax.plot(path[0], path[1], lw=2 * self.lw, color='k')

    def wire(self, wire_path, arrow=False, round_corners=None, color='k'):
        """Draw a wire/cable following a polyline, optionally rounded and arrow-tipped.

        Parameters
        ----------
        wire_path : sequence of (float, float)
            Vertices of the wire path.
        arrow : bool, optional
            If ``True``, add an arrowhead at the final vertex. Defaults to ``False``.
        round_corners : sequence of bool, optional
            One flag per vertex; where ``True`` the corner is drawn as a quadratic
            Bezier (rounded) instead of a sharp bend. Defaults to ``None`` (all sharp).
        color : color, optional
            Wire colour. Defaults to ``'k'``.
        """
        if round_corners is not None:
            codes = [Path.MOVETO]
            skip_next = True
            for w, r in zip(wire_path, round_corners):
                if skip_next:
                    skip_next = False
                    continue
                if r:
                    codes.append(Path.CURVE3)
                    skip_next = True
                else:
                    codes.append(Path.LINETO)
            codes.append(Path.LINETO)
            patch = PathPatch(Path(wire_path, codes), ec=color, fc='none', lw=2 * self.lw)
            self.ax.add_patch(patch)
        else:
            points = np.asarray(wire_path)
            self.ax.plot(points[:, 0], points[:, 1], lw=2 * self.lw, color=color)
        if arrow:
            pt2 = np.array(wire_path[-1]) + 1e-12 * (np.array(wire_path[-2]) - np.array(wire_path[-1]))
            self.ax.annotate('', xy=wire_path[-1], xytext=pt2, \
                             arrowprops=dict(width=3 * self.lw, headwidth=12 * self.lw, headlength=18 * self.lw, lw=0, color=color))

    @component("Variable coupler", "Fibers & couplers")
    def coupler(self, x, y, angle=0):
        """Draw a variable-ratio fiber coupler as a gold box with crossing fibers.

        Parameters
        ----------
        x, y : float
            Centre of the coupler.
        angle : float, optional
            Orientation in degrees. Defaults to ``0``.
        """
        width = self.component_size
        patch = Rectangle((x - width/2, y - width/2), width, width,
                          angle=angle, rotation_point='center', ec='k', \
                          fc=self.coupler_color, lw=self.lw, zorder=100)
        self.ax.add_patch(patch)
        radius = 0.3 * self.component_size
        xvals = np.linspace(-1 / np.sqrt(2), 1 - 1 / np.sqrt(2), 100) * radius + x
        # The arc only spans part of the box; values outside the disc become NaN by
        # design and are filtered out below, so ignore the expected sqrt warning.
        with np.errstate(invalid='ignore'):
            yvals = -np.sqrt(radius**2 - (xvals - (x - radius / np.sqrt(2)))**2) + y + radius / np.sqrt(2)
        xvals2 = np.linspace(-width / 2, -radius / np.sqrt(2), 50) + x
        yvals2 = -0.5 * (1 + np.tanh(4 * (xvals2 - xvals2[len(xvals2) // 2]) / (xvals2[-1] - xvals2[0]))) \
                      * (1 - 1 / np.sqrt(2)) * radius + y
        yvals3 = -np.linspace(-width / 2, -radius / np.sqrt(2), 50) + y
        xvals3 = 0.5 * (1 + np.tanh(4 * (yvals3 - yvals3[len(yvals3) // 2]) / (yvals3[-1] - yvals3[0]))) \
                     * (1 - 1 / np.sqrt(2)) * radius + x
        points = np.vstack((np.concat((xvals2, xvals, xvals3[::-1])), np.concat((yvals2, yvals, yvals3[::-1])))).T
        points1 = self.rotate(points[~np.isnan(points[:, 0]) & ~np.isnan(points[:, 1])], angle, (x, y))
        points2 = self.rotate(points[~np.isnan(points[:, 0]) & ~np.isnan(points[:, 1])], angle + 180, (x, y))
        self.ax.plot(points1[:, 0], points1[:, 1], lw=2 * self.lw, color='k', zorder=102)
        self.ax.plot(points2[:, 0], points2[:, 1], lw=2 * self.lw, color='k', zorder=102)

    @component("Laser", "Sources")
    def laser(self, x, y, angle=0, color='red'):
        """Draw a laser source: a finned housing with a coloured output aperture.

        Parameters
        ----------
        x, y : float
            Position of the output aperture (where the beam emerges).
        angle : float, optional
            Orientation in degrees; the beam exits along ``+x`` at ``angle = 0``.
            Defaults to ``0``.
        color : color, optional
            Output beam colour shading. Defaults to ``'red'``.
        """
        height = 1.5 * self.component_size
        width = 2 * self.component_size
        end_width = 0.2 * self.component_size
        end_height = 1.0 * self.component_size
        upper_rect = Rectangle((x - width, y + height / 6), width, height / 3, color='xkcd:dark', \
                               angle=angle, rotation_point=(x, y))
        lower_rect = Rectangle((x - width, y - height / 2), width, height / 3, color='xkcd:dark', \
                               angle=angle, rotation_point=(x, y))
        middle_rect = Rectangle((x - width, y - height / 6), width, height / 3, ec='k', fc='none', \
                                angle=angle, rotation_point=(x, y))
        end_rect = Rectangle((x - width - end_width, y - end_height / 2), end_width, end_height, ec='none', fc='black', \
                             angle=angle, rotation_point=(x, y))
        self.apply_gradient(middle_rect, color, 'white', 'reflected', angle=angle + 90)
        self.ax.add_patch(upper_rect)
        self.ax.add_patch(lower_rect)
        self.ax.add_patch(middle_rect)
        self.ax.add_patch(end_rect)

    @component(
        "Vacuum chamber", "Chambers & traps",
        demo=lambda od, x, y: od.vacuum_chamber(
            x, y, 0.7, 0.55,
            viewports=((x - 0.35, y), (x + 0.35, y),
                       (x, y + 0.275, 90), (x, y - 0.275, 90)),
        ),
    )
    def vacuum_chamber(self, x, y, width, height, angle=0, viewports=None):
        """Draw a rectangular vacuum chamber outline with optional viewports.

        Parameters
        ----------
        x, y : float
            Centre of the chamber.
        width, height : float
            Outer dimensions of the chamber in data units.
        angle : float, optional
            Rotation in degrees. Defaults to ``0``.
        viewports : sequence, optional
            Each entry is ``(vx, vy)`` or ``(vx, vy, rotation)`` giving the centre (and
            optional extra rotation in degrees) of a glass viewport drawn on the
            chamber wall. Defaults to ``None``.
        """
        vwidth = 0.2*self.component_size
        vheight = self.component_size
        cham = Rectangle((x - width/2, y - height/2), width, height, fc='none', \
                         ec=self.chamber_color, lw=0.7*self.data_to_points(vwidth), \
                         zorder=-1000)
        self.ax.add_patch(cham)
        if viewports:
            for viewport in viewports:
                if len(viewport) == 3:
                    rotation = viewport[-1]
                else:
                    rotation = 0
                pos = np.array(viewport[:2]) - np.array((vwidth/2, vheight/2))
                back = Rectangle(pos, vwidth, vheight, angle=angle + rotation, \
                                 rotation_point=viewport[:2], ec='none', fc='white', zorder=-10)
                self.ax.add_patch(back)
                port = Rectangle(pos, vwidth, vheight, angle=angle + rotation, \
                                 rotation_point=viewport[:2], ec=self.glass_colors[2], \
                                 lw=0, fc='none', zorder=10)
                self.apply_gradient(port, *self.glass_colors[:2], 'reflected', \
                                    alpha=self.glass_alpha, angle=angle + rotation + 90)
                self.ax.add_patch(port)

    @component(
        "Octagonal chamber", "Chambers & traps",
        demo=lambda od, x, y: od.octagonal_chamber(
            x, y, 0.75, viewports=(True, True, True, True),
        ),
    )
    def octagonal_chamber(self, x, y, width, angle=0, viewports=None):
        """Draw an octagonal vacuum chamber outline with optional face viewports.

        Parameters
        ----------
        x, y : float
            Centre of the chamber.
        width : float
            Across-flats width of the octagon in data units.
        angle : float, optional
            Rotation in degrees. Defaults to ``0``.
        viewports : sequence of bool, optional
            Four flags (for the left, top, right and bottom faces) selecting which of
            the four axis-facing windows to draw. Defaults to ``None``.
        """
        vwidth = 0.2 * self.component_size
        vheight = self.component_size
        sidelength = width / (1 + np.sqrt(2))
        points = ((x - width / 2, y - sidelength / 2), \
                  (x - width / 2, y + sidelength / 2), \
                  (x - sidelength / 2, y + width / 2), \
                  (x + sidelength / 2, y + width / 2), \
                  (x + width / 2, y + sidelength / 2), \
                  (x + width / 2, y - sidelength / 2), \
                  (x + sidelength / 2, y - width / 2), \
                  (x - sidelength / 2, y - width / 2))
        windows = ((x - width / 2, y), (x, y + width / 2), (x + width / 2, y), (x, y - width / 2))
        points = self.rotate(points, angle=angle, rotation_point=(x, y))
        windows = self.rotate(windows, angle=angle, rotation_point=(x, y))
        cham = Polygon(np.array(points), closed=True, fc='none', ec=self.chamber_color, \
                       lw=0.7 * self.data_to_points(vwidth), zorder=-1000)
        self.ax.add_patch(cham)
        if viewports:
            for i, viewport, window in zip(range(4), viewports, windows):
                if viewport:
                    pos = np.array(window) - np.array((vwidth / 2, vheight / 2))
                    back = Rectangle(pos, vwidth, vheight, angle=angle + (i % 2) * 90, \
                                     rotation_point=tuple(window), ec='none', fc='white', zorder=-10)
                    self.ax.add_patch(back)
                    port = Rectangle(pos, vwidth, vheight, angle=angle + (i % 2) * 90, \
                                     rotation_point=tuple(window), ec=self.glass_colors[2], \
                                     lw=0, fc='none', zorder=10)
                    self.apply_gradient(port, *self.glass_colors[:2], 'reflected', \
                                        alpha=self.glass_alpha, angle=angle + (i % 2) * 90 + 90)
                    self.ax.add_patch(port)

    def laser_beam(self, points, width=None, color=None, alpha=None, no_overlap=True):
        """Draw a laser beam as a translucent constant-width polyline.

        Parameters
        ----------
        points : sequence of (float, float)
            Vertices the beam passes through.
        width : float, optional
            Beam width in data units. Defaults to ``0.2 * component_size``.
        color : color, optional
            Beam colour. Defaults to :attr:`laser_color`.
        alpha : float, optional
            Beam opacity. Defaults to :attr:`laser_alpha`.
        no_overlap : bool, optional
            If ``True``, underlay an opaque white copy so overlapping translucent beam
            segments do not visibly add up. Defaults to ``True``.
        """
        if width is None:
            width = 0.2*self.component_size
        if color is None:
            color = self.laser_color
        if alpha is None:
            alpha = self.laser_alpha
        points = np.array(points)
        if no_overlap:
            self.ax.plot(points[:,0], points[:,1], color='white', \
                         lw=self.data_to_points(width), zorder=0, solid_joinstyle='bevel', \
                         solid_capstyle='butt')
        self.ax.plot(points[:,0], points[:,1], color=color, alpha=alpha, \
                     lw=self.data_to_points(width), zorder=0, solid_joinstyle='bevel', \
                     solid_capstyle='butt')

    def focused_beam(self, start, end, width1, width2, color=None, alpha=None, \
                     show_focus=True, no_overlap=True):
        """Draw a converging (or diverging) beam between two points.

        The beam is a trapezoid going from ``width1`` at ``start`` to ``width2`` at
        ``end``; with ``show_focus`` the far end crosses over to form a focus.

        Parameters
        ----------
        start, end : (float, float)
            Endpoints of the beam segment.
        width1, width2 : float
            Beam widths at ``start`` and ``end`` respectively, in data units.
        color : color, optional
            Beam colour. Defaults to :attr:`laser_color`.
        alpha : float, optional
            Beam opacity. Defaults to :attr:`laser_alpha`.
        show_focus : bool, optional
            If ``True`` the rays cross at ``end`` (a focus); if ``False`` they stay
            parallel-sided. Defaults to ``True``.
        no_overlap : bool, optional
            Underlay an opaque white copy to avoid translucent overlap. Defaults to
            ``True``.
        """
        vec = np.array(end) - np.array(start)
        length = np.linalg.norm(vec)
        angle = np.atan2(vec[1], vec[0])
        if color is None:
            color = self.laser_color
        if alpha is None:
            alpha = self.laser_alpha
        factor = 2*int(show_focus) - 1
        x1, y_z_pd = start
        x2 = x1 + length
        transform = Affine2D().rotate_around(x1, y_z_pd, angle) + self.ax.transData
        if no_overlap:
            back = Polygon(((x1, y_z_pd - width1/2), (x1, y_z_pd + width1/2), \
                            (x2, y_z_pd - factor*width2/2), (x2, y_z_pd + factor*width2/2)), \
                            fc='white', ec='none', lw=0, zorder=0, transform=transform)
            self.ax.add_patch(back)
        beam = Polygon(((x1, y_z_pd - width1/2), (x1, y_z_pd + width1/2), \
                        (x2, y_z_pd - factor*width2/2), (x2, y_z_pd + factor*width2/2)), \
                        fc=color, alpha=alpha, ec='none', lw=0, zorder=0, transform=transform)
        self.ax.add_patch(beam)

    def section_view(self, x, y, width, height, offset, angle=0):
        """Draw a section/break-out box with dashed leader lines.

        Used to draw a magnified or orthogonal cut-away of part of the layout, connected
        to the main view by dashed lines.

        Parameters
        ----------
        x, y : float
            Centre of the section line on the main view.
        width : float
            Width of the section line/box.
        height : float
            Height of the break-out box.
        offset : float
            Vertical offset from the section line to the box.
        angle : float, optional
            Rotation in degrees. Defaults to ``0``.
        """
        points = ((x - width/2, y), (x + width/2, y), \
                  (x - width/2, y + offset), (x + width/2, y + offset))
        rot = self.rotate(points, angle, (x, y))
        self.ax.plot(rot[:2, 0], rot[:2, 1], lw=2*self.lw, color='k', zorder=1000)
        self.ax.plot((rot[0, 0], rot[2, 0]), (rot[0, 1], rot[2, 1]), lw=2*self.lw, ls='--', \
                     color='k', zorder=1000)
        self.ax.plot((rot[1, 0], rot[3, 0]), (rot[1, 1], rot[3, 1]), lw=2*self.lw, ls='--', \
                     color='k', zorder=1000)
        rect = Rectangle((x - width/2, y + offset), width, height, rotation_point=(x, y), \
                         angle=angle, fc='none', ec='k', lw=2*self.lw, zorder=1000)
        self.ax.add_patch(rect)

    def rotate(self, points, angle, rotation_point):
        """Rotate points about a pivot.

        Parameters
        ----------
        points : array-like, shape (N, 2)
            Points to rotate.
        angle : float
            Rotation angle in degrees (counter-clockwise).
        rotation_point : (float, float)
            Pivot to rotate about.

        Returns
        -------
        numpy.ndarray, shape (N, 2)
            The rotated points.
        """
        angle_rad = np.deg2rad(angle)
        rot_matrix = np.array([[np.cos(angle_rad), -np.sin(angle_rad)],
                               [np.sin(angle_rad),  np.cos(angle_rad)]])

        shifted_points = points - np.array(rotation_point)
        rotated_points = shifted_points @ rot_matrix.T
        rotated_points += np.array(rotation_point)

        return rotated_points

    def apply_gradient(self, patch, color1, color2, mode='linear', alpha=1, \
                       angle=0, resolution=300, zorder=10):
        """Fill a patch with a two-colour gradient clipped to its shape.

        Renders a gradient image masked to the patch outline and adds it to the axis;
        this is what gives glass, mirrors and other elements their shading. The patch
        itself should be added with ``fc='none'`` so only its edge shows.

        Parameters
        ----------
        patch : matplotlib.patches.Patch
            The patch defining the fill region (and, for path patches, its transform).
        color1, color2 : color
            Endpoint colours of the gradient.
        mode : {'linear', 'reflected', 'radial'}, optional
            Gradient style: a straight ramp, a ramp mirrored about the centre, or a
            radial ramp from the centre outward. Defaults to ``'linear'``.
        alpha : float, optional
            Opacity of the gradient. Defaults to ``1``.
        angle : float, optional
            Direction of the gradient in degrees, for the linear/reflected modes.
            Defaults to ``0``.
        resolution : int, optional
            Pixel resolution of the gradient image per axis. Defaults to ``300``.
        zorder : float, optional
            Draw order of the gradient image. Defaults to ``10``.
        """
        transformed = isinstance(patch, PathPatch)

        transformed_path = patch.get_patch_transform().transform_path(patch.get_path())
        bbox = transformed_path.get_extents()
        xmin, xmax = bbox.xmin, bbox.xmax
        ymin, ymax = bbox.ymin, bbox.ymax

        x = np.linspace(xmin, xmax, resolution)
        y = np.linspace(ymin, ymax, resolution)
        X, Y = np.meshgrid(x, y)
        points = np.c_[X.ravel(), Y.ravel()]

        inside = transformed_path.contains_points(points)
        inside = inside.reshape((resolution, resolution))

        if mode == 'radial':
            cx = (xmin + xmax) / 2
            cy = (ymin + ymax) / 2
            dx = (xmax - xmin) / 2
            dy = (ymax - ymin) / 2
            radius = np.sqrt(dx**2 + dy**2)
            gradient = np.sqrt((X - cx)**2 + (Y - cy)**2) / radius
            gradient = np.clip(gradient, 0, 1)
        elif mode in ('linear', 'reflected'):
            theta = np.deg2rad(angle)
            vx, vy = np.cos(theta), np.sin(theta)
            cx = (xmin + xmax) / 2
            cy = (ymin + ymax) / 2
            Xc = X - cx
            Yc = Y - cy
            proj = Xc * vx + Yc * vy
            if mode == 'linear':
                min_proj = proj.min()
                max_proj = proj.max()
                gradient = (proj - min_proj) / (max_proj - min_proj)
            elif mode == 'reflected':
                max_abs = np.max(np.abs(proj))
                gradient = np.abs(proj) / max_abs

        rgba1 = np.array(to_rgba(color1, alpha=alpha)).reshape(1, 1, 4)
        rgba2 = np.array(to_rgba(color2, alpha=alpha)).reshape(1, 1, 4)
        gradient = gradient[..., np.newaxis]
        image = (1 - gradient) * rgba1 + gradient * rgba2
        image = np.squeeze(image)
        alpha_mask = np.where(inside, 1.0, 0.0)[..., np.newaxis]
        image[..., -1] *= alpha_mask[..., 0]

        transform = patch.get_transform() if transformed else self.ax.transData

        self.ax.imshow(image, extent=[xmin, xmax, ymin, ymax], origin='lower', \
                       interpolation='none', zorder=zorder, transform=transform)

    def data_to_points(self, width):
        """Convert a length in data coordinates to typographic points.

        Used so linewidths and marker sizes (specified by matplotlib in points) can be
        made to track a length expressed in data units.

        Parameters
        ----------
        width : float
            Length in data coordinates.

        Returns
        -------
        float
            The equivalent length in points (1 point = 1/72 inch), including a small
            empirical fudge factor for visual consistency.
        """
        trans = self.ax.transData.transform
        x0, y0 = trans((0, 0))
        x1, y_z_pd = trans((width, 0))
        pixel_len = np.hypot(x1 - x0, y_z_pd - y0)
        dpi = self.fig.dpi
        fudge_factor = 1.27

        return 72 * fudge_factor * pixel_len / dpi

    def annotation(self, x, y, text, arrow_pos=None, **kwargs):
        """Add a text label, optionally with an arrow pointing to a target.

        Parameters
        ----------
        x, y : float
            Position of the text.
        text : str
            Label text (may contain LaTeX/newlines).
        arrow_pos : (float, float), optional
            If given, draw an arrow from the text to this point. Defaults to ``None``.
        **kwargs
            Passed to :meth:`~matplotlib.axes.Axes.text`/``annotate``. ``fontsize``,
            ``zorder`` and ``color`` default to the canvas font size, ``1000`` and
            ``'k'`` respectively.
        """
        if 'fontsize' not in kwargs.keys():
            kwargs['fontsize'] = self.fontsize
        if 'zorder' not in kwargs.keys():
            kwargs['zorder'] = 1000
        if 'color' not in kwargs.keys():
            kwargs['color'] = 'k'
        if arrow_pos:
            self.ax.annotate(text, xytext=(x, y), xy=arrow_pos, \
                             arrowprops=dict(width=3*self.lw, headwidth=16*self.lw, \
                             headlength=20*self.lw, lw=0, color=kwargs['color']), **kwargs)
        else:
            self.ax.text(x, y, text, **kwargs)

    @component("Compass", "Diagram elements")
    def compass(self, x, y, angle=0):
        """Draw a two-axis orientation compass (an L of labelled arrows).

        Parameters
        ----------
        x, y : float
            Position of the compass origin (corner of the L).
        angle : float, optional
            Rotation in degrees. Defaults to ``0``.
        """
        length = 1.5 * self.component_size
        xvals = [x, x + length, x]
        yvals = [y, y, y + length]
        points = self.rotate(np.array((xvals, yvals)).T, angle, (x, y))
        self.ax.plot([points[0, 0], points[1, 0]], [points[0, 1], points[1, 1]], color='k', lw=2 * self.lw)
        self.ax.plot([points[0, 0], points[2, 0]], [points[0, 1], points[2, 1]], color='k', lw=2 * self.lw)
        self.ax.plot(points[1, 0], points[1, 1], ms=10 * self.lw, marker=(3, 0, angle - 90), color='k')
        self.ax.plot(points[2, 0], points[2, 1], ms=10 * self.lw, marker=(3, 0, angle), color='k')
        self.ax.plot(x, y, 'o', ms=15 * self.lw, mec='k', mew=2 * self.lw, mfc='white')
        self.ax.plot(x, y, '.', ms=2 * self.lw, color='k')
