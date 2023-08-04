"""Parts which help build accurate mocks"""
from collections import UserList
from typing import TypeVar, overload, Tuple, Optional, Iterable, Dict, Sequence, Union, Any
from unittest.mock import NonCallableMock

from pyglet.graphics import Group, Batch
from pyglet.graphics.vertexdomain import VertexList, IndexedVertexList

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


def _build_unindexed_config(
        count: int,
        mode: int,
        batch: Optional[Batch],
        group: Optional[Group],
        data: Dict[str, Tuple[str, Iterable[T]]]
) -> Dict[str, Union[FakeCTypesArray[T], Batch, Group, int]]:
    """Build kwargs to configure the attributes of a mock VertexList.

    Pass the result to :py:meth:`unittest.Mock.configure_mock` via
    `**` unpacking. Since this is a test helper, it only validates
    the value of `count`.

    Returns:
        A dict ready to set the attributes of a VertexList mock.
    """
    if count < 1:
        raise ValueError(f"Count should be >= 1, but got {count}")

    config = {
        'count': count,
        'mode': mode,
        'batch': batch,
        'group': group
    }
    for name, fmt_data in data.items():
        _, pure_data = fmt_data
        config[name] = FakeCTypesArray(pure_data)

    return config


def mock_vertex_list(
        count: int,
        mode: int,
        batch: Optional[Batch] = None,
        group: Optional[Group] = None,
        **data: Tuple[str, Iterable]
) -> VertexList:
    """A mock version of `ShaderProgram.vertex_list`"""

    vertex_list = NonCallableMock(spec=VertexList)
    vertex_list.configure_mock(**_build_unindexed_config(
       count, mode, batch, group, data
    ))

    return vertex_list


def mock_indexed_vertex_list(
        count: int,
        mode: int,
        indices: Sequence[int],
        batch: Optional[Batch] = None,
        group: Optional[Group] = None,
        **data: Tuple[str, Iterable]
) -> IndexedVertexList:
    """A mock version of `ShaderProgram.indexed_vertex_list`"""

    new_list = NonCallableMock(spec=IndexedVertexList)
    config: Dict[str, Any] = _build_unindexed_config(count, mode, batch, group, data)
    config['indices'] = indices

    new_list.configure_mock(**config)
    return new_list
