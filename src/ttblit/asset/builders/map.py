from .raw import RawAsset


class MapAsset(RawAsset):
    command = 'map'
    help = 'Convert popular tilemap formats for 32Blit'
    types = ['tiled']
    typemap = {
        'tiled': ('.tmx', '.raw'),
    }

    def tiled_to_binary(self, input_data):
        from xml.etree import ElementTree as ET
        root = ET.fromstring(input_data)
        layers = root.findall('layer/data')
        data = []
        for layer in layers:
            try:
                data.append(self.csv_to_binary(
                    layer.text,
                    base=10,
                    offset=-1))  # Tiled indexes from 1 rather than 0
            except ValueError:
                raise RuntimeError("Failed to convert .tmx, does it contain blank (0) tiles? Tiled is 1-indexed, so these get converted to -1 and blow everyting up")
        return b''.join(data)

    def to_binary(self, input_data):
        if self.input_type == 'tiled':
            return self.tiled_to_binary(input_data)
