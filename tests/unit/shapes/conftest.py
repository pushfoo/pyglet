from pytest import fixture


@fixture(autouse=True)
def dummmy_shaders_for_modules() -> str:
    return "pyglet.shapes"
