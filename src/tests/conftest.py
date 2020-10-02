import argparse

import pytest


@pytest.fixture
def parsers():
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true', help='Enable exception traces')
    return parser, parser.add_subparsers(dest='command', help='Commands')