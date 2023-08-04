"""Parts which help build accurate mocks"""
from collections import UserList
from typing import TypeVar, overload, Tuple

T = TypeVar('T')


class FakeCtypesArray(UserList[T]):
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
