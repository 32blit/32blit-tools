import argparse

import pytest


@pytest.fixture
def subparser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true', help='Enable exception traces')
    return parser.add_subparsers(dest='command', help='Commands')


def test_raw_csv_to_binary(subparser):
    from ttblit.asset import raw

    raw = raw.RawAsset(subparser)

    raw.prepare_options({
        'input_type': 'csv',
        'symbol_name': 'csv'  # Since we're not supplying an input file, an empty symbol_name will fail
    })
    output = raw.to_binary('''1, 2, 3,
4, 5, 6,
7, 8, 9''')

    assert output == b'\x01\x02\x03\x04\x05\x06\x07\x08\x09'
