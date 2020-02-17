from ttblit.core import AssetBuilder

class Map(AssetBuilder):
    command = 'map'
    help = 'Convert popular tilemap formats for 32Blit'
    types = ['tiled']
    typemap = {
        'tiled': ('.tmx', '.raw'),
    }