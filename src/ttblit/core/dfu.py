import pathlib
import zlib

import construct
from construct import (Checksum, Const, CString, Flag, GreedyBytes,
                       GreedyRange, Hex, Int8ul, Int16ul, Int32ul, Padded,
                       Padding, Prefixed, RawCopy, Rebuild, Struct, len_, this)

DFU_SIGNATURE = b'DfuSe'
DFU_size = Rebuild(Int32ul, 0)


def DFU_file_length(ctx):
    '''Compute the entire file size + 4 bytes for CRC
    The total DFU file length is ostensibly the actual
    length in bytes of the resulting file.
    However DFU File Manager does not seem to agree,
    since it's output size is 16 bytes short.
    Since this is suspiciously the same as the suffix
    length in bytes, we omit that number to match
    DFU File Manager's output.
    '''
    size = 11        # DFU Header Length
    # size += 16     # DFU Suffix Length
    for target in ctx.targets:
        # Each target has a 274 byte header consisting
        # of the following fields:
        size += Const(DFU_SIGNATURE).sizeof()          # szSignature ('Target' in bytes)
        size += Int8ul.sizeof()                        # bAlternateSetting
        size += Int8ul.sizeof()                        # bTargetNamed
        size += Padding(3).sizeof()                    # Padding
        size += Padded(255, CString('utf8')).sizeof()  # szTargetName
        size += Int32ul.sizeof()                       # dwTargetSize
        size += Int32ul.sizeof()                       # dwNbElements
        size += DFU_target_size(target)

    return size


def DFU_target_size(ctx):
    '''Returns the size of the target binary data, plus the
    dwElementAddress header, and dwElementSize byte count.
    '''
    size = 0

    try:
        images = ctx.images
    except AttributeError:
        images = ctx['images']

    size += sum([DFU_image_size(image) for image in images])
    return size


def DFU_image_size(image):
    return len(image['data']) + Int32ul.sizeof() + Int32ul.sizeof()


DFU_image = Struct(
    'dwElementAddress' / Hex(Int32ul),     # Data offset address for image
    'data' / Prefixed(Int32ul, GreedyBytes)
)

DFU_target = Struct(
    'szSignature' / Const(b'Target'),      # DFU target identifier
    'bAlternateSetting' / Int8ul,          # Gives device alternate setting for which this image can be used
    'bTargetNamed' / Flag,                 # Boolean determining if the target is named
    Padding(3),                            # Mystery bytes!
    'szTargetName' / Padded(255, CString('utf8')),         # Target name
                                                           # DFU File Manager does not initialise this
                                                           # memory, so our file will not exactly match
                                                           # its output.
    'dwTargetSize' / Rebuild(Int32ul, DFU_target_size),    # Total size of target images
    'dwNbElements' / Rebuild(Int32ul, len_(this.images)),  # Count the number of target images
    'images' / GreedyRange(DFU_image)
)

DFU_body = Struct(
    'szSignature' / Const(DFU_SIGNATURE),  # DFU format identifier (changes on major revisions)
    'bVersion' / Const(1, Int8ul),         # DFU format revision   (changes on minor revisions)
    'DFUImageSize' / Rebuild(Int32ul, DFU_file_length),    # Total DFU file length in bytes
    'bTargets' / Rebuild(Int8ul, len_(this.targets)),      # Number of targets in the file

    'targets' / GreedyRange(DFU_target),

    'bcdDevice' / Int16ul,                 # Firmware version, or 0xffff if ignored
    'idProduct' / Hex(Int16ul),            # USB product ID or 0xffff to ignore
    'idVendor' / Hex(Int16ul),             # USB vendor ID or 0xffff to ignore
    'bcdDFU' / Const(0x011A, Int16ul),     # DFU specification number
    'ucDfuSignature' / Const(b'UFD'),      # 0x44, 0x46 and 0x55 ie 'DFU' but reversed
    'bLength' / Const(16, Int8ul)          # Length of the DFU suffix in bytes
)

DFU = Struct(
    'fields' / RawCopy(DFU_body),
    'dwCRC' / Checksum(Int32ul,            # CRC calculated over the whole file, except for itself
                       lambda data: 0xffffffff ^ zlib.crc32(data),
                       this.fields.data)
)


def display_dfu_info(parsed):
    print(f'''
Device: {parsed.fields.value.bcdDevice}
Target: {parsed.fields.value.idProduct:04x}:{parsed.fields.value.idVendor:04x}
Size: {parsed.fields.value.DFUImageSize:,} bytes
Targets: {parsed.fields.value.bTargets}''')
    for target in parsed.fields.value.targets:
        print(f'''
    Name: {target.szTargetName}
    Alternate Setting: {target.bAlternateSetting}
    Size: {target.dwTargetSize:,} bytes
    Images: {target.dwNbElements}''')
        for image in target.images:
            print(f'''
        Offset: {image.dwElementAddress}
        Size: {len(image.data):,} bytes
''')


def build(input_file, output_file, address, force=False, id_product=0x0000, id_vendor=0x0483):
    if not output_file.parent.is_dir():
        raise RuntimeError(f'Output directory "{output_file.parent}" does not exist!')
    elif output_file.is_file() and not force:
        raise RuntimeError(f'Existing output file "{output_file}", use --force to overwrite!')

    if not input_file.suffix == ".bin":
        raise RuntimeError(f'Input file "{input_file}", is not a .bin file?')

    output = DFU.build({'fields': {'value': {
        'targets': [{
            'bAlternateSetting': 0,
            'bTargetNamed': True,
            'szTargetName': 'ST...',
            'images': [{
                'dwElementAddress': address,
                'data': open(input_file, 'rb').read()
            }]
        }],
        'bcdDevice': 0,
        'idProduct': id_product,
        'idVendor': id_vendor
    }}})

    open(output_file, 'wb').write(output)


def read(input_file):
    try:
        return DFU.parse(open(input_file, 'rb').read())
    except construct.core.ConstructError as error:
        RuntimeError(f'Invalid dfu file {input_file} ({error})')


def dump(input_file, force=False):
    parsed = read(input_file)

    for target in parsed.fields.value.targets:
        target_id = target.bAlternateSetting
        for image in target.images:
            address = image.dwElementAddress
            data = image.data
            dest = str(input_file).replace('.dfu', '')
            filename = f"{dest}-{target_id}-{address}.bin"

            if pathlib.Path(filename).is_file() and not force:
                raise RuntimeError(f'Existing output file "{filename}", use --force to overwrite!')

            print(f"Dumping image at {address} to {filename} ({len(data)} bytes)")

            open(filename, 'wb').write(data)
