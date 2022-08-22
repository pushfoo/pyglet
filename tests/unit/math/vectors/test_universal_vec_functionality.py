"""
Test behavior expected of all vector classes.
"""

import pytest
from . import (
    ALL_VEC_PAIRINGS,
    ALL_VEC_PAIRINGS_DICT,
    ALL_VEC_LENGTHS,
    externalize_to_operator_method
)

from operator import add, sub, mul, truediv, neg


@pytest.fixture(params=[
    add, sub, mul, truediv,
    externalize_to_operator_method('lerp', 0.5),
])
def binary_vec_operator_returning_new(request):
    return request.param


@pytest.fixture(params=[neg, round])
def unary_vec_operator_returning_new(request):
    return request.param


@pytest.fixture(params=ALL_VEC_PAIRINGS)
def vec_pairing(request):
    return request.param


@pytest.fixture
def vec_type(vec_pairing):
    return vec_pairing[0]


@pytest.fixture
def vec_length(vec_type):
    return ALL_VEC_LENGTHS[vec_type]


@pytest.fixture
def vec_coords(vec_length):
    return tuple((0.0 for n in range(vec_length)))


@pytest.fixture
def vec_instance(vec_type, vec_coords):
    return vec_type(*vec_coords)


@pytest.fixture
def right_vec_type(vec_type):
    return ALL_VEC_PAIRINGS_DICT[vec_type]


@pytest.fixture
def right_vec_length(right_vec_type):
    return ALL_VEC_LENGTHS[right_vec_type]


@pytest.fixture
def right_vec_coords(vec_length):
    # use all ones to avoid dividing by zero for truediv operator
    return tuple((1.0 * (n + 1) for n in range(vec_length)))


@pytest.fixture
def right_vec_instance(right_vec_type, right_vec_coords):
    return right_vec_type(*right_vec_coords)


def test_repr(right_vec_type, right_vec_coords, right_vec_instance):
    result = repr(right_vec_instance)
    expected = f"{right_vec_type.__name__}({', '.join(map(str, right_vec_coords))})"
    assert result == expected


# AKA the "freeze from the left rule" or left-hand typing rule in doc
def test_binary_vec_ops_return_vec_of_same_type_as_left_operand(
        vec_instance, right_vec_instance,
        binary_vec_operator_returning_new
):
    result = binary_vec_operator_returning_new(vec_instance, right_vec_instance)
    assert isinstance(result, type(vec_instance))


def test_unary_ops_return_vec_of_same_type_as_instance(
        vec_type,
        vec_instance,
        unary_vec_operator_returning_new
):
    result = unary_vec_operator_returning_new(vec_instance)
    assert isinstance(result, vec_type)

