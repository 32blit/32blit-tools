import pytest
import argparse


@pytest.fixture
def subparser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true', help='Enable exception traces')
    return parser.add_subparsers(dest='command', help='Commands')


def test_raw_csv(subparser):
    from ttblit.asset import raw

    raw = raw.RawAsset(subparser)

    output = raw.csv_to_binary('''1, 2, 3,
4, 5, 6,
7, 8, 9''')

    assert output == b'\x01\x02\x03\x04\x05\x06\x07\x08\x09'
