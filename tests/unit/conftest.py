import re
from typing import Tuple, Callable, Union, Dict, cast
from unittest.mock import NonCallableMagicMock, Mock

import pytest
from pytest import fixture

from pyglet import gl
from pyglet.gl import ObjectSpace
from pyglet.graphics import Batch, Group
from pyglet.graphics.shader import ShaderProgram
from tests.base.mock_helpers import (
    DummyShader,
    DummyShaderProgram,
    get_shallow_shader_mock
)


@fixture
def generic_dummy_shader_program():
    """A basic mock shader for when you don't need fine-grained accuracy.

    It does not provide any parsing services.
    """
    return get_shallow_shader_mock()


@fixture
def dummy_shader_getter(generic_dummy_shader_program: ShaderProgram):
    """
    Provide a dummy getter to monkeypatch getters for default shaders.

    Drawable objects in pyglet usually use one or more default shaders.
    They are usually accessed through a top-level function named
    something like ``get_default_shader`` in their implementing module.

    If no GL context exists, calling that function creates one, which
    risks unit tests for non-drawing features failing or running slower
    than they should.

    This fixture helps prevent that. It can be used in one of two ways:

    1. Providing a `monkeypatch_fixtures_in` fixture for
       `monkeypatch_all_shaders` to use.
    2. Directly monkeypatching shaders yourself.

    Although the first option is preferable, you can do the second as
    follows::

        @fixture(autouse=True)  # Force this to be used for every test
        def monkeypatch_default_sprite_shader(monkeypatch, dummy_shader_getter):
            monkeypatch.setattr(
                'pyglet.sprite.get_default_shader',
                 dummy_shader_getter)

    """
    # A named function instead of a lambda for clarity in debugger views.
    def get_dummy_shader(*args, **kwargs):
        return get_shallow_shader_mock()

    return get_dummy_shader

# May be redundant and removable after PR finished
# Identify module elements which are likely to return shaders.
SHADER_GETTER_PATTERN = re.compile(r"^get(_[a-zA-Z0-9]+)*_shader$")


# May be redundant and removable after PR finished
def is_shader_getter(c: Callable) -> bool:
    """Returns true if an item appears to be a shader getter.

    Args:
       c: A callable to evaluate
    Returns:
       Whether an item appears to be a shader getter.
    """
    if not (hasattr(c, "__name__") and SHADER_GETTER_PATTERN.fullmatch(c.__name__)):
        return False

    if not callable(c):
        raise TypeError(f"{c} is not callable despite being named like a shader getter")

    return True


@pytest.fixture
def mock_batch_factory() -> Callable:
    """A callable which returns Batch mocks for tests.

    The default value is a callable Mock to provide developers
    with access to the call history during debugging.
    """
    return Mock(side_effect=lambda : NonCallableMagicMock(spec=Batch))


@pytest.fixture
def mock_group_factory() -> Callable:
    """A callable which returns Group mocks for tests.

    The default value is a callable Mock to provide developers
    with access to the call history during debugging.
    """
    return Mock(side_effect=lambda : NonCallableMagicMock(spec=Group))


@pytest.fixture
def default_context_object_space():
    """A garbage collection record keeper of "doomed" objects.

    It appears safe to first mock, then ignore for any non-drawing
    (i.e. unit) tests.
    """
    return NonCallableMagicMock(spec=ObjectSpace)


@pytest.fixture
def pyglet_graphics_default_group(mock_group_factory):
    """A mock to assign to the corresponding name on the context"""
    return mock_group_factory()


@pytest.fixture
def pyglet_graphics_default_batch(mock_batch_factory):
    """A mock to assign to the corresponding name on the context"""
    return mock_batch_factory()


# TODO: finish work on porting to new automock shader system
@pytest.fixture
def default_gl_context(
        pyglet_graphics_default_group,
        pyglet_graphics_default_batch,
        default_context_object_space
):
    """A per-test GL context with the attribute names above set.

    .. warning:: Never use ``spec_set`` to build Context mocks!

                 It will cause all tests for modules with on-demand
                 loading of default shaders to fail. The current
                 design of pyglet sets and reads attributes after
                 Context object creation, which is the behavior
                 ``spec_set`` exists to forbid.

    If you need more detail than this fixture's default arguments
    or behavior can provide, override them per the docstring of
    :py:func:`.autopatch_shaders`.

    Args:
         pyglet_graphics_default_group:
            A mock to use as the returned context's default group.
         pyglet_graphics_default_batch:
            A mock to use as the returned context's default batch.

    Returns:
        A Mock of gl.Context with the passed values as its defaults
    """
    ctx = NonCallableMagicMock(spec=gl.Context)
    ctx.attach_mock(pyglet_graphics_default_group, 'pyglet_graphics_default_group')
    ctx.attach_mock(pyglet_graphics_default_batch, 'pyglet_graphics_default_batch')
    # TODO: did this work without the following present? Can it be made to?
    # shouldn't mock speccing implicitly take care of it?
    ctx.attach_mock(default_context_object_space, 'object_space')

    return ctx


# TODO: verify this should be set to autouse
@pytest.fixture(autouse=True)
def gl_automock_config():
    return {}  # Uses default settings


@pytest.fixture(autouse=True)
def autopatch_shaders(
        monkeypatch,
        gl_automock_config,
        mock_batch_factory,
        default_gl_context
):
    """Replace the shader classes with auto-configuring mock types.

    .. warning:: The default settings make multiple assumptions of tests!

    .. _overriding:: https://docs.pytest.org/en/7.4.x/how-to/fixtures.html#overriding-fixtures-on-various-levels

    Use `pytest's documentation on overriding fixtures <overriding_>`_
    to help you any of the assumptions below create problems for you:

    .. list-table::
        :header-rows: 1

        * - Assumption
          - Way(s) to Address

        * - The default values for :py:func:`.default_gl_context`
            are acceptable.

          - Override the fixtures below:

            * :py:func:`pyglet_graphics_default_group`
            * :py:func:`pyglet_graphics_default_batch`
            * :py:func:`default_context_object_space`

            If you need even greater control, you can override
            :py:func:`default_gl_context` entirely.

        * - Only one simulated window and context are needed.
          - Build custom mock fixtures.

        * - Tests only need the vertex attributes of shaders.
          - 1. Extend the partial shader parsing implementation in
               :py:module:`tests.base.shader_parse_helpers`
            2. Ask for help doing so
            3. Use the fallback shader patching tools.


    TODO: review this design further. This might be brittle and bad.

    ============ ========= =====================================
    Reserved key Default   Action
    ============ ========= =====================================
    ``ctx``      ``True``  Patch the GL context
    ``shaders``  ``True``  Patch the shader classes if ``True``.


    Args:
        monkeypatch: pytest's built-in monkeypatch fixture.
        gl_autospec_config: A dict of config options.
    """
    config: Dict[str, Union[bool, str]] = dict(
        ctx=default_gl_context,
        shaders=True)

    # Can be empty dict or None
    if gl_automock_config:
        config.update(gl_automock_config)

    if config_ctx := config['ctx']:
        monkeypatch.setattr("pyglet.gl.current_context", config_ctx)

    monkeypatch.setattr('pyglet.graphics.Batch', mock_batch_factory)

    if config['shaders']:
        def _patch_shader_part(name, class_):
            monkeypatch.setattr(f"pyglet.graphics.shader.{name}", class_)

        _patch_shader_part("Shader", DummyShader)
        _patch_shader_part("ShaderProgram", DummyShaderProgram)



# Color constants & fixtures for use with Shapes, UI elements, etc.
ORIGINAL_RGB_COLOR = 253, 254, 255
ORIGINAL_RGBA_COLOR = ORIGINAL_RGB_COLOR + (37,)
NEW_RGB_COLOR = 1, 2, 3
NEW_RGBA_COLOR = 5, 6, 7, 59


@fixture(scope="session")
def original_rgb_color():
    return ORIGINAL_RGB_COLOR


@fixture(scope="session")
def original_rgba_color():
    return ORIGINAL_RGBA_COLOR


@fixture(params=[ORIGINAL_RGB_COLOR, ORIGINAL_RGBA_COLOR])
def original_rgb_or_rgba_color(request):
    return request.param


def expected_alpha_for_color(color: Tuple[int, ...]):
    """
    Slow but readable color helper with validation.

    This uses more readable logic than the main library and will raise
    clear ValueErrors as part of validation.

    Args:
        color: An RGB or RGBA color

    Returns:

    """
    num_channels = len(color)

    if num_channels == 4:
        return color[3]
    elif num_channels == 3:
        return 255

    raise ValueError(
        f"Expected color tuple with 3 or 4 elements, but got {color!r}.")


@fixture
def original_rgb_or_rgba_expected_alpha(original_rgb_or_rgba_color):
    return expected_alpha_for_color(original_rgb_or_rgba_color)


@fixture(scope="session")
def new_rgb_color():
    return NEW_RGB_COLOR


@fixture(scope="session")
def new_rgba_color():
    return NEW_RGBA_COLOR


@fixture(params=[NEW_RGB_COLOR, NEW_RGBA_COLOR])
def new_rgb_or_rgba_color(request):
    return request.param
