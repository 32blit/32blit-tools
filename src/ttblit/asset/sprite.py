from ttblit.core import AssetBuilder

class Sprite(AssetBuilder):
    command = 'sprite'
    help = 'Convert an image file into an RGBA palette-based 32Blit sprite'
    types = ['image']
    typemap = {
        'image': ('.png', '.gif')
    }