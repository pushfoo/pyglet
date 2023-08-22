"""
Simulate enough of shader compilation to make reasonably accurate mocks.

What: Compute attribute array lengths
Why : Make vertex list mocks with correct lengths
How : Regex, as suggested by Benjamin

Non-block uniforms are detected but ignored since they don't seem necessary
for unit tests.
"""
from __future__ import annotations

import re
from typing import Dict, Set, Optional, Mapping, Union, Final

# Import a bunch of GL constants to use pre-existing lookup tables
from pyglet.gl import GL_BOOL, GL_BOOL_VEC2, GL_BOOL_VEC3, GL_BOOL_VEC4, GL_INT_VEC2, GL_UNSIGNED_INT, \
    GL_UNSIGNED_INT_VEC3, GL_UNSIGNED_INT_VEC2, GL_INT_VEC4, GL_INT_VEC3, GL_INT, GL_UNSIGNED_INT_VEC4, GL_FLOAT, \
    GL_FLOAT_VEC2, GL_FLOAT_VEC3, GL_FLOAT_VEC4, GL_DOUBLE, GL_DOUBLE_VEC2, GL_DOUBLE_VEC3, GL_DOUBLE_VEC4


from pyglet.graphics.shader import _attribute_types
from tests.base.counting import SharedOrderBase

# Uniform blocks aren't even handled because they dont seem to affect unit tests
GL_ATTRIBUTE_REGEX = re.compile(r"in\s+(?P<type>[a-zA-Z0-9_-]+)\s+(?P<name>[a-zA-Z0-9_-]+)\s*;")
GL_UNIFORM_VAR_REGEX = re.compile(r"uniform\s+(?P<type>[a-zA-Z0-9_-]+)\s+(?P<name>[a-zA-Z0-9_-]+)\s*;")

_qualifier_to_pattern = {
    'uniform': GL_UNIFORM_VAR_REGEX,
    'attribute': GL_ATTRIBUTE_REGEX
}


_qualifier_to_allowed_shader_types: Mapping[str, Set] = {
    'uniform': {
        'vertex',
        'fragment',
        'compute'  # examples/opengl/compute_shader.py indicates uniforms are allowed
    },
    'attribute': {
        'vertex',
        'compute'  # same source file as above indicates they are allowed here
    }
}


# Allow indirect use of using shader._attribute_types to get tuples of
# (count, format) to approximate GLSL compiler output + shader queries.
_type_name_to_id: Final[Dict[str, int]] = {

    'bool':  GL_BOOL,
    'bvec2': GL_BOOL_VEC2,
    'bvec3': GL_BOOL_VEC3,
    'bvec4': GL_BOOL_VEC4,

    'int':   GL_INT,
    'ivec2': GL_INT_VEC2,
    'ivec3': GL_INT_VEC3,
    'ivec4': GL_INT_VEC4,

    'uint':  GL_UNSIGNED_INT,
    'uvec2': GL_UNSIGNED_INT_VEC2,
    'uvec3': GL_UNSIGNED_INT_VEC3,
    'uvec4': GL_UNSIGNED_INT_VEC4,

    'float': GL_FLOAT,
    'vec2':  GL_FLOAT_VEC2,
    'vec3':  GL_FLOAT_VEC3,
    'vec4':  GL_FLOAT_VEC4,

    'double': GL_DOUBLE,
    'dvec2':  GL_DOUBLE_VEC2,
    'dvec3':  GL_DOUBLE_VEC3,
    'dvec4':  GL_DOUBLE_VEC4

}


def parse_shader_entries(
        source: str,
        qual_to_pattern: Mapping[str, re.Pattern] = _qualifier_to_pattern
) -> Dict[str, Dict[str, str]]:
    """
    Psuedo-parsing of shader attributes & non-block uniforms.

    It only extracts uniforms and uniform blocks.

    Args:
        source: The shader source to psuedo-parse.
        qual_to_pattern: A mapping specifying how to parse each type of
            qualifier.

    Returns:
        A Dict[qualifier_type: str, Dict[name: str, data_type: str]].
    """
    results = {}

    # Reverse the order of the parse.
    for qual_type, regex in qual_to_pattern.items():
        qual_dict = {m.group('name'):m.group('type') for m in regex.finditer(source)}
        results[qual_type] = qual_dict

    return results


def validate_parsed(
        shader_type: str,
        qualifier_type: str,
        parsed: Mapping[str, str]
) -> Optional[str]:
    """
    Return an error string if something doesn't seem allowed in a shader.

    Args:
        shader_type: The type of this shader as a string, i.e. 'vertex'.
        qualifier_type: The qualifier type the parse results are for.
        parsed: May be an empty mapping. Any parsed variable names along with their data type.

    Returns:
        ``None`` if there are 0 parsed items or if they are allowed for
         this qualifier type. Otherwise, an error message.
    """
    if len(parsed) == 0\
       or qualifier_type not in (allowed_in := _qualifier_to_allowed_shader_types[qualifier_type]):
        return None

    found = ', '.join(f"{qualifier_type} {data} {name}" for data, name in parsed.items())
    allowed_str = ', '.join(allowed_in)

    return f"Parsing a {shader_type} shader, but found inappropriate " \
           f"qualifier{'s' if len(found) > 1 else ''}:\n{found}"\
           f"\n{qualifier_type} is allowed in these shader types:\n" \
           f"{allowed_str}."


class PretendAllocator(SharedOrderBase):
    """
    Return non-overlapping pointers

    Helps mock glGetAttribLocation's behavior.
    """

    _next_value: int = 1
    _calls: Dict[str, int] = dict()

    @classmethod
    def next_value(cls, to_c_string: str):
        """
        Return a fake pointer & advance the internal pointer by len + 1.

        Args:
            to_c_string: A string to encode to UTF-8 and append a
                null byte to.

        Returns:
            A pointer in an imaginary, manually managed memory space.
        """
        location = cls._next_value

        as_c_string = f"{to_c_string.encode('utf-8')}\0"
        c_string_len = len(as_c_string)
        cls._next_value += c_string_len
        cls._calls[as_c_string] = c_string_len

        return location


def build_attributes(attributes: Mapping[str, str]) -> Dict[str, Dict[str, Union[int, str]]]:
    """
    Generate reasonable approximations of attribute descriptions.

    This is a rough stand-in for the GLSL compiler + gl calls such as
    glGetAttribLocation.

    Args:
        attributes: A mapping of attribute variable names to their
            corresponding type identifiers.

    Returns:
        A dictionary mapping attribute names to approximate compiled
        properties such as format string, count, and size.
    """
    parsed = {}
    for a_name, a_type in attributes.items():
        _type_id = _type_name_to_id[a_type]

        # gl_type_enum_int -> count: int, fmt: str
        count, fmt = _attribute_types[_type_id]
        parsed[a_name] = dict(
            type=_type_id,
            # This is an approximate guess based on size = 1 for most values
            # in the debugger and the khronos.org Data Type (GLSL) page:
            # https://www.khronos.org/opengl/wiki/Data_Type_(GLSL)#Scalars
            size=1 if 'd' not in fmt else 2,
            location=PretendAllocator.next_value(a_name),
            count=count,
            format=fmt
        )

    return parsed




