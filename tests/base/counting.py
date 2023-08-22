from __future__ import annotations


class SharedOrderBase:
    """
    Subclass this to create a mixin type with auto-advancing values.
    """

    # This will be overridden, but it's here to help with typing
    _next_value: int = 0

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._next_value = 0

    @classmethod
    def reset_value(cls, base_id: int = 0) -> None:
        cls._next_value = base_id

    def next_value(self) -> int:
        cls = self.__class__
        current_id = cls._next_value
        cls._next_value += 1
        return current_id


