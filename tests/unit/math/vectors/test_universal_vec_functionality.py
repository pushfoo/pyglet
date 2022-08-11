"""
Test behavior expected of all vector classes.
"""

import pytest
from . import ALL_VEC_PAIRINGS, ALL_VEC_LENGTHS, ALL_VEC_TYPES, externalize_to_operator_method

from operator import add, sub, mul, truediv


@pytest.fixture(params=[
    add, sub, mul, truediv,
    externalize_to_operator_method('lerp', 0.5),
])
def binary_vec_operator_returning_new(request):
    return request.param


@pytest.mark.parametrize("vec_type", ALL_VEC_TYPES)
def test_repr(vec_type):
    num_dimensions = ALL_VEC_LENGTHS[vec_type]
    coords = [float(i) for i in range(1, num_dimensions + 1)]
    v = vec_type(*coords)
    assert repr(v) == f"{vec_type.__name__}({', '.join(map(str, coords))})"


# AKA the "freeze from the left rule" or left-hand typing rule in doc
@pytest.mark.parametrize("left_hand_type,right_hand_type", ALL_VEC_PAIRINGS)
def test_binary_ops_return_vec_of_same_type_as_left_operand(
        left_hand_type, right_hand_type,
        binary_vec_operator_returning_new
):
    num_dimensions = ALL_VEC_LENGTHS[left_hand_type]

    left = left_hand_type(*[0.0 for n in range(num_dimensions)])
    # use all ones to avoid dividing by zero for truediv operator
    right = right_hand_type(*[1.0 for n in range(num_dimensions)])
    result = binary_vec_operator_returning_new(left, right)
    assert isinstance(result, left_hand_type)


