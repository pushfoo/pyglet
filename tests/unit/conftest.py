import importlib
import inspect
import re
from typing import Tuple, Callable, Iterable, Union
from unittest.mock import NonCallableMagicMock

from pytest import fixture

from pyglet.graphics.shader import ShaderProgram
from tests.base.mock_helpers import mock_vertex_list, mock_indexed_vertex_list


@fixture
def generic_dummy_shader_program():
    """A basic mock shader for when you only need basic GL attributes.

    It does not provide fine-grained control of attributes or uniforms.
    """
    program = NonCallableMagicMock(spec=ShaderProgram)
    program.configure_mock(
        vertex_list=mock_vertex_list,
        indexed_vertex_list=mock_indexed_vertex_list
    )

    return program


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
        return generic_dummy_shader_program

    return get_dummy_shader


# Identify module elements which are likely to return shaders.
SHADER_GETTER_PATTERN = re.compile(r"^get(_[a-zA-Z0-9]+)*_shader$")


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


def monkeypatch_all_shaders(
        monkeypatch_shaders_in: Union[Iterable[str], str],
        monkeypatch,
        dummy_shader_getter
):
    """Monkeypatch all shaders in the specified module(s).

    Declare a `monkeypatch_shaders_in` fixture in either a conftest.py
    or test file to use no-op shaders during unit tests.

    For each module string, every top-level member named get*_shader
    will be monkeypatched with get_dummy_shader_program.

    Example usage::

        # in a test file dealing with sprites
        @pytest.fixture
        def dummy_shaders_for_modules() -> str:
            return "pyglet.sprite"

        # multiple modules
        @pytest.fixture
        def dummy_shaders_for_modules() -> Tuple[str]:
            return (
                "pyglet.sprite",
                "pyglet.text.layout"
            )

    Args:
        monkeypatch_shaders_in:
            A string or iterable of strings representing the target modules.
        monkeypatch:
            The pytest monkeypatch fixture.
        dummy_shader_getter:
            The default dummy shader getter.
    """
    if isinstance(monkeypatch_shaders_in, str):
        monkeypatch_shaders_in = [monkeypatch_shaders_in]

    # Iterate over modules
    for module_name in monkeypatch_shaders_in:
        module = importlib.import_module(module_name)

        # Monkeypatch anything which looks like a shader getter
        for member_name, member in inspect.getmembers(module, is_shader_getter):
            monkeypatch.setattr(f"{module_name}.{member_name}", dummy_shader_getter)


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
