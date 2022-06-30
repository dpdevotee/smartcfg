import os

import pytest


@pytest.fixture
def set_env():
    variables = set()

    def _set_env(name, value):
        variables.add(name)
        os.environ[name] = value

    yield _set_env

    for v in variables:
        os.environ.pop(v, None)
