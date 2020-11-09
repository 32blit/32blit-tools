import argparse
import logging
import pathlib
import struct

from PIL import Image


class Colour():
    def __init__(self, colour):
        if type(colour) is Colour:
            self.r, self.g, self.b = colour
        elif len(colour) == 6:
            self.r, self.g, self.b = tuple(bytes.fromhex(colour))
        elif ',' in colour:
            self.r, self.g, self.b = [int(c, 10) for c in colour.split(',')]

    def __getitem__(self, index):
        return [self.r, self.g, self.b][index]


class Palette():
    def __init__(self, palette_file=None):
        self.transparent = None
        self.entries = []

        if type(palette_file) is Palette:
            self.transparent = palette_file.transparent
            self.entries = palette_file.entries
            return

        if palette_file is not None:
            palette_file = pathlib.Path(palette_file)
            palette_type = palette_file.suffix[1:]

            palette_loader = f'load_{palette_type}'

            fn = getattr(self, palette_loader, None)
            if fn is None:
                self.load_image(palette_file)
            else:
                fn(palette_file, open(palette_file, 'rb').read())

            self.extract_palette()

    def extract_palette(self):
        self.entries = []
        for y in range(self.height):
            for x in range(self.width):
                self.entries.append(self.image.getpixel((x, y)))

    def set_transparent_colour(self, r, g, b):
        if (r, g, b, 0xff) in self.entries:
            self.transparent = self.entries.index((r, g, b, 0xff))
            self.entries[self.transparent] = (r, g, b, 0x00)
            return self.transparent
        return None

    def load_act(self, palette_file, data):
        # Adobe Colour Table .act
        palette = data
        if len(palette) < 772:
            raise ValueError(f'palette {palette_file} is not a valid Adobe .act (length {len(palette)} != 772')

        size, _ = struct.unpack('>HH', palette[-4:])
        self.width = 1
        self.height = size
        self.image = Image.frombytes('RGB', (self.width, self.height), palette).convert('RGBA')

    def load_pal(self, palette_file, data):
        # Pro Motion NG .pal - MS Palette files and raw palette files share .pal suffix
        # Raw files are just 768 bytes
        palette = data
        if len(palette) < 768:
            raise ValueError(f'palette {palette_file} is not a valid Pro Motion NG .pal')
        # There's no length in .pal files, so we just create a 16x16 256 colour palette
        self.width = 16
        self.height = 16
        self.image = Image.frombytes('RGB', (self.width, self.height), palette).convert('RGBA')

    def load_gpl(self, palette_file, data):
        palette = data
        palette = palette.decode('utf-8').strip()
        if not palette.startswith('GIMP Palette'):
            raise ValueError(f'palette {palette_file} is not a valid GIMP .gpl')
        # Split the whole file into palette entries
        palette = palette.split('\r\n')
        # drop 'GIMP Palette' from the first entry
        palette.pop(0)

        # calculate our image width/height here because len(palette)
        # equals the number of palette entries
        self.width = 1
        self.height = len(palette)

        # Split out the palette entries into R, G, B and drop the hex colour
        # This convoluted list comprehension does this while also flatenning to a 1d array
        palette = [int(c) for entry in palette for c in entry.split('\t')[:-1]]
        self.image = Image.frombytes('RGB', (self.width, self.height), bytes(palette)).convert('RGBA')

    def load_image(self, palette_file):
        palette = Image.open(palette_file)
        self.width, self.height = palette.size
        if self.width * self.height > 256:
            raise argparse.ArgumentError(None, f'palette {palette_file} has too many pixels {self.width}x{self.height}={self.width*self.height} (max 256)')
        logging.info(f'Using palette {palette_file} {self.width}x{self.height}')

        self.image = palette.convert('RGBA')

    def get_entry(self, r, g, b, a, remap_transparent=True, strict=False):
        if (r, g, b, a) in self.entries:
            index = self.entries.index((r, g, b, a))
            return index
            # Noisy print
            # logging.info(f'Re-mapping ({r}, {g}, {b}, {a}) at ({x}x{y}) to ({index})')
        # Anything with 0 alpha that's not in the palette might as well be the transparent colour
        elif a == 0 and self.transparent is not None:
            return self.transparent
        elif not strict:
            # Set this as the transparent colour if we don't have one
            if a == 0 and self.transparent is None:
                self.transparent = len(self.entries) - 1

            if len(self.entries) < 256:
                self.entries.append((r, g, b, a))
                return len(self.entries) - 1
            else:
                raise TypeError('Out of palette entries')
        else:
            raise TypeError(f'Colour {r}, {g}, {b}, {a} does not exist in palette!')

    def tolist(self):
        result = []
        for r, g, b, a in self.entries:
            result.append(r)
            result.append(g)
            result.append(b)
            result.append(a)
        return result

    def tobytes(self):
        return bytes(self.tolist())

    def tostruct(self):
        result = []
        for r, g, b, a in self.entries:
            result.append({
                'r': r,
                'g': g,
                'b': b,
                'a': a,
            })
        return result

    def bit_length(self):
        return max(1, len(self.entries) - 1).bit_length()

    def __len__(self):
        return len(self.entries)

    def __getitem__(self, index):
        return self.entries[index]


def type_palette(palette_file):
    # Only used as a type in argparse.
    # This wrapper around Palette traps errors and
    # raises in a way that's visible to the user
    if type(palette_file) is Palette:
        return palette_file

    try:
        return Palette(palette_file)
    except TypeError as e:
        raise argparse.ArgumentTypeError(None, str(e))
    except ValueError as e:
        raise argparse.ArgumentError(None, str(e))
