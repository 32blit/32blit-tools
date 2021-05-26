import struct


def test_map_tiled():
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

    assert output == b'\x00\x00'


def test_map_tiled_struct_8bit():
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
    assert output == struct.pack('<4sHHHHHH4B', b'MTMX', 16, 0, 0, 4, 1, 1, 0, 1, 2, 3)


def test_map_tiled_struct_16bit():
    from ttblit.asset.builders import map

    output = map.map.build('''<?xml version="1.0" encoding="UTF-8"?>
<map version="1.2" tiledversion="1.3.2" orientation="orthogonal" renderorder="right-down" compressionlevel="-1" width="4" height="1" tilewidth="8" tileheight="8" infinite="0" nextlayerid="2" nextobjectid="1">
 <layer id="1" name="Tile Layer 1" width="1" height="1">
  <data encoding="csv">
256,257,258,259
</data>
 </layer>
</map>
''', 'tiled', output_struct=True)
    # Tile indexes 256, 257, 258, 259 will be remapped -1 to 255, 256, 257, 258
    # output tile data will be 16bit!
    assert output == struct.pack('<4sHHHHHH4H', b'MTMX', 16, 1, 0, 4, 1, 1, 255, 256, 257, 258)


def test_map_tiled_layer_reorder():
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
    assert output == struct.pack('<4sHHHHHH8B', b'MTMX', 16, 0, 0, 4, 1, 2, 0, 1, 2, 3, 4, 5, 6, 7)


def test_map_empty_tiled_remap_empty():
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

    assert output == b'\x00\xFF\x00\x00'
