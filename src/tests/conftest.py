import pathlib

import pytest


@pytest.fixture
def test_resources(request):
    # Get path to "test_relocs" resource dir
    return pathlib.Path(request.module.__file__).with_suffix('')
