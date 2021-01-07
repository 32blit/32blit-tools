import argparse
import struct

import pytest


@pytest.fixture
def subparser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true', help='Enable exception traces')
    return parser.add_subparsers(dest='command', help='Commands')


def test_map_tiled(subparser):
    from ttblit.asset.builders import map

    output = map.map.build('''<?xml version="1.0" encoding="UTF-8"?>
<map version="1.2" tiledversion="1.3.2" orientation="orthogonal" renderorder="right-down" compressionlevel="-1" width="1" height="1" tilewidth="8" tileheight="8" infinite="0" nextlayerid="2" nextobjectid="1">
 <layer id="1" name="Tile Layer 1" width="1" height="1">
  <data encoding="csv">
1
</data>
 </layer>
</map>
''', 'tiled')

    assert output == b'\x00'


def test_map_tiled_struct(subparser):
    from ttblit.asset.builders import map

    output = map.map.build('''<?xml version="1.0" encoding="UTF-8"?>
<map version="1.2" tiledversion="1.3.2" orientation="orthogonal" renderorder="right-down" compressionlevel="-1" width="4" height="1" tilewidth="8" tileheight="8" infinite="0" nextlayerid="2" nextobjectid="1">
 <layer id="1" name="Tile Layer 1" width="1" height="1">
  <data encoding="csv">
1,2,3,4
</data>
 </layer>
</map>
''', 'tiled', output_struct=True)
    # Tile indexes 1, 2, 3, 4 will be remapped -1 to 0, 1, 2, 3
    assert output == struct.pack('<4sBHHH4B', b'MTMX', 0, 4, 1, 1, 0, 1, 2, 3)


def test_map_tiled_layer_reorder(subparser):
    from ttblit.asset.builders import map

    output = map.map.build('''<?xml version="1.0" encoding="UTF-8"?>
<map version="1.2" tiledversion="1.3.2" orientation="orthogonal" renderorder="right-down" compressionlevel="-1" width="4" height="1" tilewidth="8" tileheight="8" infinite="0" nextlayerid="2" nextobjectid="1">
 <layer id="2" name="Tile Layer 2" width="4" height="1">
  <data encoding="csv">
5,6,7,8
</data>
 </layer>
 <layer id="1" name="Tile Layer 1" width="4" height="1">
  <data encoding="csv">
1,2,3,4
</data>
 </layer>
</map>
''', 'tiled', output_struct=True)
    assert output == struct.pack('<4sBHHH8B', b'MTMX', 0, 4, 1, 2, 0, 1, 2, 3, 4, 5, 6, 7)


def test_map_empty_tiled_remap_empty(subparser):
    from ttblit.asset.builders import map

    output = map.map.build('''<?xml version="1.0" encoding="UTF-8"?>
<map version="1.2" tiledversion="1.3.2" orientation="orthogonal" renderorder="right-down" compressionlevel="-1" width="2" height="1" tilewidth="8" tileheight="8" infinite="0" nextlayerid="2" nextobjectid="1">
 <layer id="1" name="Tile Layer 1" width="1" height="1">
  <data encoding="csv">
1,0
</data>
 </layer>
</map>
''', 'tiled', empty_tile=255)

    assert output == b'\x00\xFF'
