.. _migration:

Migrating from pyglet 2.0
=========================
pyglet 2.1 contains several small, but breaking changes. Some of these are
usibility improvements, and some are in the interest of improving the quality
of the code base. If you are upgrading from pyglet 2.0 and your game or project
has suddenly stopped working, this is the place for you. The following sections
should hopefully get you up and running again without too much effort. If you
are having an issue that is not covered here, please open up an issue ticket on
`Github <https://github.com/pyglet/pyglet/issues>`_ so that we can add it.

Window "HiDPI" support
----------------------
TBD

Labels & Text Layouts
---------------------
The positional argument order for text Labels and Layouts was not consistent
in previous pyglet releases. This has been refactored to make things more
consistent, with the goal of making it easier to switch between Layouts or
create custom subclasses. All layouts now start with the same positional
argument ordering::

    TextLayout(document, x, y, z, width, height, anchor_x, anchor_y, rotation, ...)
    ScrollableTextLayout(document, x, y, z, width, height, anchor_x, anchor_y, rotation, ...)
    IncrementalTextLayout(document, x, y, z, width, height, anchor_x, anchor_y, rotation, ...)

The Label classes also follow a similar default argument ordering, with one
small exception: Label and HTMLLabel take "text" as the first argument instead
of "document". Other than that, the rest of the positional arguments line up::

    DocumentLabel(document, x, y, z, width, height, anchor_x, anchor_y, rotation, ...)
    Label(text, x, y, z, width, height, anchor_x, anchor_y, rotation, ...)
    HTMLLabel(text, x, y, z, width, height, anchor_x, anchor_y, rotation, ...)

The layouts and lables don't share all of the same argument, so the rest of the
arguments will need to be provided as usual, where they differ. Please see the
API documents for full details.

Shapes
------
For consistency with the rest of the library, it was decided to represent
all angles in degrees instead of radians. Previously we had a mix of both,
which lead to some confusion. Using degrees also makes the API consistent
with Sprites and other rotatable objects.

The arguments for :py:class:`~pyglet.shapes.Line` have changed slightly.
Instead of "width", we now use "thickness". This matches with other shapes
that are made up of line segments. For example the :py:class:`~pyglet.shapes.Box`
shape, which already uses "width" (and height) to mean it's overall size.
Going forward, any shape that is made up of lines should use `thickness`
for the width of those lines.

Controllers
-----------
The Controller interface has been changed slightly. Analog sticks and dpad
events now dispatch :py:class:`~pyglet.math.Vec2`, instead of individual float
or boolean values. This can potentially save a few lines of code, and gives
easy access to several helper methods found on the Vec classes. For instance,
where you had to do this in the past::

    @controller.event
    def on_dpad_motion(controller, dpleft, dpright, dpup, dpdown):
        if dpleft:
            # move left
        if dpright:
            # move right
        if dpright and dpdown:
            # move diagonal, but have to normalize the values by yourself

You now get a Vec2 instead of booleans that can be used directly::

    @controller.event
    def on_dpad_motion(controller, vector):
        player_position += vector * PLAYER_SPEED
        # Easily normalize for diagonal values:
        player_position += vector.normalize() * PLAYER_SPEED

Vectors can also be useful for analog sticks, because it gives an easy way to
calculate dead-zones using `abs`. For example::

    @controller.event
    def on_stick_motion(controller, name, vector):
        if abs(vector) <= DEADZONE:
            return
        elif name == "leftstick":
            # Do something with the 2D vector
        elif name == "rightstick":
            # Do something with the 2D vector

Normalization of vectors can also be useful for some analog sticks. When dealing
with Controllers that have non-circular gates, the The absolute values of their
combined x and y axis can sometimes exceed 1.0. Vector normalization can ensure
that the maximum value stays within range. For example::

            vector = min(vector, vector.normalize())

You can also of course directly access the individual `Vec2.x` & `Vec2.y`
attributes. See :py:class:`~pyglet.math.Vec2` for more details on vector types.

Gui
---

All widget events now dispatch the widget instance itself as the first argument.
This is similar to how Controller/Joystick events are implemented. In cases where
the same handler function is set to multiple widgets, this gives a way to determine
which widget has dispatched the event.

The :py:class:`~pyglet.gui.widget.ToggleButton` and :py:class:`~pyglet.gui.widget.PushButton`
widgets have a small change. Instead of the image arguments being named "pressed"
and "depressed", they has been renamed to the correct "pressed" and "unpressed".

Math module
-----------
In the :py:mod:`~pyglet.math` module, vector types (:py:class:`~pyglet.math.Vec2`,
:py:class:`~pyglet.math.Vec3`, :py:class:`~pyglet.math.Vec4`) are now
immutable; all operations will return a new object. In addition, all vector
objects are now hashable. This has performance benefits, and matches how the Matrix
types are implemented. For all intents and purposes, the Vec types can be treated
as tuples.

Canvas module
-------------
The `pyglet.canvas` module has been renamed to `pyglet.display`, as the canvas
concept was never fully fleshed out. The canvas concept appears to have been
meant to allow arbitrary renderable areas. This can now be easily accomplished
with Framebuffers. The name `display` is a more accurate representation of what
the code in the module actually relates to. The usage is the same, minus the
name change::

    my_display = pyglet.canvas.get_display()     # old pyglet 2.0
    my_display = pyglet.display.get_display()    # new pyglet 2.1

