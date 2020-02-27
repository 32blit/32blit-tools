import argparse

import pytest


@pytest.fixture
def subparser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true', help='Enable exception traces')
    return parser.add_subparsers(dest='command', help='Commands')


def test_map_tiled(subparser):
    from ttblit.asset import map

    map = map.MapAsset(subparser)

    output = map.tiled_to_binary('''<?xml version="1.0" encoding="UTF-8"?>
<map version="1.2" tiledversion="1.3.2" orientation="orthogonal" renderorder="right-down" compressionlevel="-1" width="1" height="1" tilewidth="8" tileheight="8" infinite="0" nextlayerid="2" nextobjectid="1">
 <layer id="1" name="Tile Layer 1" width="1" height="1">
  <data encoding="csv">
1
</data>
 </layer>
</map>
''')

    assert output == b'\x00'
