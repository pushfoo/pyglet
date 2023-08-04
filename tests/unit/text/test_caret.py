from unittest.mock import Mock, NonCallableMock

import pytest

from pyglet.graphics.vertexdomain import IndexedVertexList
from pyglet.text import layout, caret
from pyglet.text.document import UnformattedDocument
from tests.base.mock_helpers import FakeCtypesArray


@pytest.fixture(autouse=True)
def disable_automatic_caret_blinking(monkeypatch):
    monkeypatch.setattr(caret, 'clock', Mock(spec=caret.clock))


# Brittle tangle of mocks due to tightly coupled Caret/Layout design
@pytest.fixture
def mock_layout(raw_dummy_shader):

    # Rename to be closer to implementation code
    program = raw_dummy_shader

    # Allow the shader program to create a mock vertex list on demand
    def _fake_vertex_list_method(count, mode, batch=None, group=None, colors=None):
        vertex_list = NonCallableMock(spec=IndexedVertexList)
        vertex_list.colors = FakeCtypesArray(colors[1])
        return vertex_list

    program.vertex_list = _fake_vertex_list_method
    # Create layout mock using a caret-compatible layout classes
    _layout = NonCallableMock(spec=layout.IncrementalTextLayout)

    group = NonCallableMock(spec=layout.IncrementalTextDecorationGroup)
    group.attach_mock(program, 'program')
    _layout.attach_mock(group, 'foreground_decoration_group')

    _layout.attach_mock(NonCallableMock(spec=UnformattedDocument), 'document')

    return _layout


# Color fixtures are defined in pyglet's tests/unit/conftest.py
@pytest.fixture
def rgba_caret(mock_layout, original_rgba_color):
    return caret.Caret(layout=mock_layout, color=original_rgba_color)


@pytest.fixture
def rgb_caret(mock_layout, original_rgb_color):
    return caret.Caret(layout=mock_layout, color=original_rgb_color)


@pytest.fixture
def rgb_or_rgba_caret(mock_layout, original_rgb_or_rgba_color):
    return caret.Caret(layout=mock_layout, color=original_rgb_or_rgba_color)


def test_init_sets_opacity_to_255_when_rgb_color_argument(rgb_caret):
    assert rgb_caret.color[3] == 255


def test_init_sets_opacity_from_rgba_value_as_color_argument(rgba_caret, original_rgba_color):
    assert rgba_caret.color[3] == original_rgba_color[3]


def test_init_sets_rgb_channels_correctly(rgb_or_rgba_caret, original_rgb_or_rgba_color):
    assert rgb_or_rgba_caret.color[:3] == original_rgb_or_rgba_color[:3]


def test_color_setter_sets_rgb_channels_correctly(rgb_or_rgba_caret, new_rgb_or_rgba_color):
    rgb_or_rgba_caret.color = new_rgb_or_rgba_color
    assert rgb_or_rgba_caret.color[:3] == new_rgb_or_rgba_color[:3]


def test_color_setter_preserves_alpha_channel_when_setting_rgb_colors(
    rgb_or_rgba_caret,
    original_rgb_or_rgba_expected_alpha,
    new_rgb_color
):
    rgb_or_rgba_caret.color = new_rgb_color
    assert rgb_or_rgba_caret.color[3] == original_rgb_or_rgba_expected_alpha


def test_color_setter_changes_alpha_channel_when_setting_rgba_colors(
    rgb_or_rgba_caret,
    new_rgba_color
):
    rgb_or_rgba_caret.color = new_rgba_color
    assert rgb_or_rgba_caret.color[3] == new_rgba_color[3]
