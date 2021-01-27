import argparse
import pathlib

import pytest


@pytest.fixture
def parsers():
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true', help='Enable exception traces')
    return parser, parser.add_subparsers(dest='command', help='Commands')


@pytest.fixture
def test_resources(request):
    # Get path to "test_relocs" resource dir
    return pathlib.Path(request.module.__file__).parent / 'resources'
