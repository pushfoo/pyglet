from itertools import product
from typing import Iterable, Tuple, Callable

from pyglet.math import Vec2, Vec3, Vec4


def all_class_versions(baseclass: type) -> Tuple[type, ...]:
    version_list = [baseclass]
    version_list.extend(baseclass.__subclasses__())
    return tuple(version_list)


def generate_all_pairings(base: Iterable):
    return tuple(product(base, base))


# This approach is ugly and verbose, but it's immutable aside from the
# length dict and allows importing only what a specific test file needs.
VEC2_TYPES = all_class_versions(Vec2)
VEC3_TYPES = all_class_versions(Vec3)
VEC4_TYPES = all_class_versions(Vec4)
ALL_VEC_TYPES = VEC2_TYPES + VEC3_TYPES + VEC4_TYPES
ALL_VEC_LENGTHS = {_type: len(_type()) for _type in ALL_VEC_TYPES}


VEC2_PAIRINGS = generate_all_pairings(VEC2_TYPES)
VEC3_PAIRINGS = generate_all_pairings(VEC3_TYPES)
VEC4_PAIRINGS = generate_all_pairings(VEC4_TYPES)
ALL_VEC_PAIRINGS = VEC2_PAIRINGS + VEC3_PAIRINGS + VEC4_PAIRINGS
ALL_VEC_PAIRINGS_DICT = {k: v for k, v in ALL_VEC_PAIRINGS}


def externalize_instance_method(method_name: str) -> Callable:
    """Return a function which calls a specific function name

    This doesn't use `functools.partial` because its goal is to mimic
    the functions in the `operators` module to help test math operations.

    :param method_name: the method to call
    :param arg_values:
    :param kwarg_values:
    :return:
    """
    def externalized(instance, *args, **kwargs):
        return getattr(instance, method_name)(*args, **kwargs)

    externalized.__name__ = f"externalized_{method_name}"

    return externalized


def externalize_to_operator_method(method_name: str, *args, **kwargs) -> Callable:
    """Return a method akin to those in the `operators` module.

    The functions in the `operators` module, such as `add`,
    call a corresponding method on their first argument, using any
    additional arguments as operators if applicable. This function
    is similar in that it returns functions which will call
    `method_name` on their first argument. The `args` passed to the
    outer function will be passed after any positional arguments

    The returned function will call the named function using ``args``
    and ``kwargs``. However, the returned will only take a left and
    right operand.

    :Parameters:
        `method_name` : str
            The method the returned function will call on its left
            operand.
        `args` : list
            What positional arguments, if any, will be passed after the
            right operand to the named method.
        `kwargs` : dict
            What keyword arguments, if any, will be passed after the right
            operand to the named method.
    """
    raw_externalized = externalize_instance_method(method_name)

    def externalized(a, b):
        return raw_externalized(a, b, *args, **kwargs)

    # store metadata somewhere accessible to the debugger
    name_elts = [str(arg) for arg in args]
    name_elts.extend([f"{k}-{str(v)}" for k, v in kwargs.items()])
    externalized.__name__ = f"{raw_externalized.__name__}_{'_'.join(name_elts)}"

    return externalized
