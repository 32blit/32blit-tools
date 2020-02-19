from ttblit.core import AssetBuilder


class Image(AssetBuilder):
    command = 'image'
    help = 'Convert an image file into raw RGB/RGBA data for 32Blit'
    types = ['image']
    typemap = {
        'image': ('.png', '.gif')
    }
