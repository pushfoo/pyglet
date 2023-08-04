import importlib
import inspect
import re
from typing import Tuple, Callable, Iterable, Union, Dict, Any
from unittest.mock import MagicMock

from pytest import fixture

from pyglet.graphics.shader import ShaderProgram


@fixture
def raw_dummy_shader():
    program = MagicMock(spec=ShaderProgram)
    program.attributes = {}
    return program


@fixture
def dummy_shader_with_attributes(raw_dummy_shader, shader_attributes: Dict[str, Any]):
    for attr_name, attr_value in shader_attributes:
        setattr(raw_dummy_shader, attr_name, attr_value)
    return raw_dummy_shader


@fixture
def get_dummy_shader_program(raw_dummy_shader):
    """
    Provide a dummy getter to monkeypatch getters for default shaders.

    By default, batchable objects create or re-use a default shader
    program. This is usually done through a ``get_default_shader``
    function on their implementing module. If no GL context exists,
    calling that function creates one, which risks non-drawing tests
    failing or running slower than optimal.

    Avoid that by passing this fixture to local monkey patching fixtures
    in module-specific single test files or conftest.py instances for
    test modules::

        # Example from ./test_sprite.py

        @fixture(autouse=True)  # Force this to be used for every test in the module
        def monkeypatch_default_sprite_shader(monkeypatch, get_dummy_shader_program):
            monkeypatch.setattr(
                'pyglet.sprite.get_default_shader',
                 get_dummy_shader_program)

    """
    # A named function instead of a lambda for clarity in debugger views.
    def _get_dummy_shader_program(*args, **kwargs):
        return raw_dummy_shader

    return _get_dummy_shader_program


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


# Easy blanket replacement of shaders
def monkeypatch_all_shaders(dummy_shaders_for_modules: Union[Iterable[str], str], monkeypatch, get_dummy_shader_program):
    """Monkeypatch all shaders in the specified modules.

    Specify a `modules_to_path` fixture in either a conftest.py or test file
    to use no-op shaders during unit tests.

    Any callable member of a named module which has a name of get*_shader
    will be replaced with the dummy shader program getter during tests.

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
        dummy_shaders_for_modules: A string or iterable of strings representing the target modules.
        monkeypatch: the pytest monkeypatch fixture.
        get_dummy_shader_program: The default dummy shader getter.
    """
    if isinstance(dummy_shaders_for_modules, str):
        dummy_shaders_for_modules = [dummy_shaders_for_modules]

    # Iterate over modules
    for module_name in dummy_shaders_for_modules:
        module = importlib.import_module(module_name)

        # Monkeypatch anything which looks like a shader getter
        for member_name, member in inspect.getmembers(module, is_shader_getter):
            monkeypatch.setattr(f"{module_name}.{member_name}", get_dummy_shader_program)


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
