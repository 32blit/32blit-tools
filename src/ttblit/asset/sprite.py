from ttblit.core import AssetBuilder

class Sprite(AssetBuilder):
    command = 'sprite'
    help = 'Convert an image file into an RGBA palette-based 32Blit sprite'
    types = ['image']
    typemap = {
        'image': ('.png', '.gif')
    }

    def image_to_c_header(self, input_data, variable=None):
        return 'some c header'