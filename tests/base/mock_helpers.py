"""Parts which help build accurate mocks"""
from __future__ import annotations

from collections import UserList
from functools import partial
from typing import TypeVar, overload, Tuple, Optional, Iterable, Dict, Union, Any, Mapping
from unittest.mock import NonCallableMock

from pyglet.graphics import Group, Batch
from pyglet.graphics.shader import (
    Shader,
    ShaderException,
    ShaderProgram,
)
from pyglet.graphics.vertexdomain import VertexList, IndexedVertexList
from tests.base.counting import SharedOrderBase
from tests.base.shader_parse_helpers import parse_shader_entries, validate_parsed, build_attributes

T = TypeVar('T')


class FakeCTypesArray(UserList[T]):
    """Imitates the way ctypes arrays return tuples when sliced.

    It makes tests cleaner by allowing direct comparisons to tuple
    values and slices of them. One example of this is colors.
    """

    @overload
    def __getitem__(self, index: int) -> T:
        ...

    @overload
    def __getitem__(self, item: slice) -> Tuple[T]:
        ...

    def __getitem__(self, item):
        if isinstance(item, slice):
            return tuple(super().__getitem__(item))

        return super().__getitem__(item)

    @classmethod
    def filled_with(cls, item: T, size: int) -> FakeCTypesArray[T]:
        return FakeCTypesArray([item] * size)

    @classmethod
    def uninitialized(cls, size: int) -> FakeCTypesArray[Optional[T]]:
        """Return an instance full of ``None``s.

        This is intended to help detect operations on uninitialized memory.

        Args:
            size: How long the array should be.

        Returns:
            An instance full of ``None``s.
        """
        return FakeCTypesArray([None] * size)


AttributeTuple = Tuple[
    int,  # type
    int,  # int
    Any,  #  ??
    int,  #  count
    str,  # format
]


def _build_unindexed_mock_config(
        base_shader_attributes: Dict[str, Dict[str, AttributeTuple]],
        count: int,
        mode: int,
        batch: Optional[Batch],
        group: Optional[Group],
        data: Dict[str, Tuple[str, Iterable[T]]]
) -> Dict[str, Union[FakeCTypesArray[T], Batch, Group, int]]:
    """Build kwargs to configure the attributes of a mock VertexList.

    Use ``**`` to unpack the return value as keyword arguments to
    :py:meth:`unittest.Mock.configure_mock`. Since this is a test helper,
    it:

    * Validates the count as > 0 since creating 0 vertices makes no sense.
    * Fills uninitialized memory with ``None`` to help

    Args:
        base_shader_attributes: a parsed dict to copy from

    Returns:
        A dict ready to set the attributes of a VertexList mock.
    """
    if count < 1:
        raise ValueError(f"Count should be >= 1, but got {count}")

    config = dict(count=count, mode=mode, batch=batch, group=group)

    # Populate
    for name, fmt in data.items():
        if isinstance(fmt, tuple):
            fmt, array = fmt

        elif isinstance(fmt, str):
            # spicy typeerror surprise if memory is uninitialized.
            array = [None] * count
        else:
            raise TypeError(
                f"Processing attribute {name!r}:"
                f" unexpected fmt type {type(fmt)}: {fmt}")

        config[name] = FakeCTypesArray(array)

    # Set missing values to Nones
    missing = set(base_shader_attributes).difference(set(data))
    for name in missing:
        config[name] = FakeCTypesArray.uninitialized(count)

    return config


def mock_vertex_list(
        base_shader_attributes: Dict,
        count: int,
        mode: int,
        batch: Optional[Batch] = None,
        group: Optional[Group] = None,
        **data: Tuple[str, Iterable]
) -> VertexList:
    """A mock version of `ShaderProgram.vertex_list`"""

    vertex_list = NonCallableMock(spec=VertexList)
    vertex_list.configure_mock(**_build_unindexed_mock_config(
       base_shader_attributes,
       count, mode, batch, group, data
    ))

    return vertex_list


def get_mock_vertex_list_builder(base_shader_attributes: Dict):
    return partial(mock_vertex_list, base_shader_attributes)


def mock_indexed_vertex_list(
        base_shader_attributes: Dict,
        count: int,
        mode: int,
        indices: Iterable[int],
        batch: Optional[Batch] = None,
        group: Optional[Group] = None,
        **data: Tuple[str, Iterable]
) -> IndexedVertexList:
    """A mock version of `ShaderProgram.indexed_vertex_list`"""

    new_list = NonCallableMock(spec=IndexedVertexList)

    # Same as above but we add the indices first
    config: Dict[str, Any] = _build_unindexed_mock_config(
        base_shader_attributes,
        count, mode, batch, group, data)
    config['indices'] = list(indices)

    new_list.configure_mock(**config)
    return new_list


def get_mock_indexed_vertex_list_builder(base_shader_attributes: Dict):
    return partial(mock_indexed_vertex_list, base_shader_attributes)


class ShaderIDMixin(SharedOrderBase):
    """Auto-incrementing shader ID mix-in."""
    pass


def get_shallow_shader_mock() -> NonCallableMock:
    """
    Returns a very low fidelity shader mock.

    This exists for a few edge cases where it's not worth caring about
    accuracy. In most cases, you'll be better off with either of the
    following:

    * Shader auto-patching through the monkeypatch_all_shaders fixture
    * Directly specifying source through the DummyShader and DummyShader
      classes below.

    Returns:
        A NonCallableMock with vertex list creation methods.

    """
    program = NonCallableMock(spec=ShaderProgram)
    program.configure_mock(
        vertex_list=get_mock_vertex_list_builder({}),
        indexed_vertex_list=get_mock_vertex_list_builder({})
    )

    return program


class DummyShader(Shader, ShaderIDMixin):
    """Replace the normal Shader."""

    def __init__(self, source_string: str, shader_type: str): # noqa
        # Match
        self._attributes = {}
        self._uniforms = {}

        self.type = shader_type
        self._id = self.next_value()
        self.source = source_string

        self.parse_results = parse_shader_entries(source_string)

        # Make sure we don't have disallowed qualifiers for the shader type
        for qual_type, qual_entries in self.parse_results.items():
            if err := validate_parsed(shader_type, qual_type, qual_entries):
               raise ShaderException(err, qual_entries)
            setattr(self, f"_{qual_type}s", qual_entries)

        return  # A place to put a breakpoint


class DummyShaderProgram(ShaderProgram, ShaderIDMixin):
    """A fake shader program which approximates GLSL parsing."""

    def __init__(self, *shaders: DummyShaderProgram):
        self._shaders = shaders

        self._id = self.next_value()
        self._attributes = {}

        # unused in current tests aside from preventing errors
        # on property access.
        self._uniforms = {}
        self._uniform_blocks = {}  # not even parsed

        raw_attributes = {}
        for shader in shaders:
            if shader._uniforms:
                self._uniforms.update(shader._uniforms)
            if shader._attributes:
                raw_attributes.update(shader._attributes)
        self._attributes.update(build_attributes(raw_attributes))
        pass

    def _check_for_missing_attributes(self, **data) -> Optional[str]:
        missing = set(data.keys()).difference(self._attributes.keys())

        if not missing:
            return None

        return  f"The following attributes don't exist: {', '.join(missing)}."\
                f"Valid names: \n{list(self._attributes)}"

    def vertex_list(self, count, mode, batch=None, group=None, **data):
        mock_list = mock_vertex_list(
            self._attributes,
            count, mode, batch=batch, group=group, **data)
        return mock_list


    def vertex_list_indexed(self, count, mode, indices, batch=None, group=None, **data):
        mock_indexed_list = mock_indexed_vertex_list(
            self._attributes,
            count, mode, indices, batch=batch, group=group, **data)
        return mock_indexed_list

    @classmethod
    def from_sources_and_types(cls, *source_and_types: Union[Iterable[Tuple[str, str]], Mapping[str, str]]):
        """Allow easier manual creation of shaders"""
        if isinstance(source_and_types, Mapping):
            source_and_types = source_and_types.items()
        return cls(*(DummyShader(*pair) for pair in source_and_types))



if __name__ == "__main__":
    from textwrap import dedent

    compute_src = dedent("""#version 430 core
    layout (local_size_x = 1, local_size_y = 1, local_size_z = 1) in;

    layout(rgba32f) uniform image2D img_output;

    void main() {
        vec4 value = vec4(0.0, 0.0, 0.0, 1.0);
        ivec2 texel_coord = ivec2(gl_GlobalInvocationID.xy);
        value.r = float(texel_coord.x)/(gl_NumWorkGroups.x);
        value.g = float(texel_coord.y)/(gl_NumWorkGroups.y);

        imageStore(img_output, texel_coord, value);
    }
    """)

    for i in range(3):
        d = DummyShader(f"{i}", 'vertex')
        assert d._id == i

    another = DummyShader(compute_src, 'compute')
    assert another._uniforms['img_output'] == 'image2D'

