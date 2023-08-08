import pytest


@pytest.fixture(autouse=True)
def monkeypatch_shaders_in() -> str:
   return "pyglet.text.layout"
