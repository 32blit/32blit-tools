import logging
import pathlib
import struct
import time

import serial.tools.list_ports
from construct.core import ConstructError
from serial.serialutil import SerialException
from tqdm import tqdm

from ..core.struct import struct_blit_meta_standalone
from ..core.tool import Tool


class Flasher(Tool):
    command = 'flash'
    help = 'Flash a binary or save games/files to 32Blit'

    def __init__(self, subparser):
        Tool.__init__(self, subparser)

        self.parser.add_argument('--port', help='Serial port', type=self.validate_comport)

        operations = self.parser.add_subparsers(dest='operation', help='Flasher operations')

        self.op_save = operations.add_parser('save', help='Save a game/file to your 32Blit')
        self.op_save.add_argument('--file', type=pathlib.Path, required=True, help='File to save')
        self.op_save.add_argument('--directory', type=str, default='/', help='Target directory')

        self.op_flash = operations.add_parser('flash', help='Flash a game to your 32Blit')
        self.op_flash.add_argument('--file', type=pathlib.Path, required=True, help='File to flash')

        self.op_delete = operations.add_parser('delete', help='Delete a game/file from your 32Blit')
        group = self.op_delete.add_mutually_exclusive_group(required=True)
        group.add_argument('--offset', type=int, help='Flash offset of game to delete')
        group.add_argument('--block', type=int, help='Flash block of game to delete')

        self.op_list = operations.add_parser('list', help='List games/files on your 32Blit')
        self.op_debug = operations.add_parser('debug', help='Enter serial debug mode')
        self.op_reset = operations.add_parser('reset', help='Reset your 32Blit')
        self.op_info = operations.add_parser('info', help='Get 32Blit run status')

    def find_comport(self):
        ret = []
        for comport in serial.tools.list_ports.comports():
            if comport.vid == 0x0483 and comport.pid == 0x5740:
                logging.info(f'Found 32Blit on {comport.device}')
                ret.append(comport.device)

        if ret:
            return ret

        raise RuntimeError('Unable to find 32Blit')

    def validate_comport(self, device):
        if device.lower() == 'auto':
            return self.find_comport()[:1]
        if device.lower() == 'all':
            return self.find_comport()

        for comport in serial.tools.list_ports.comports():
            if comport.device == device:
                if comport.vid == 0x0483 and comport.pid == 0x5740:
                    logging.info(f'Found 32Blit on {comport.device}')
                    return [device]
                # if the user asked for a port with no vid/pid assume they know what they're doing
                elif comport.vid is None and comport.pid is None:
                    logging.info(f'Using unidentified port {comport.device}')
                    return [device]
        raise RuntimeError(f'Unable to find 32Blit on {device}')

    def run(self, args):
        if args.operation is not None:
            dispatch = f'run_{args.operation}'
            getattr(self, dispatch)(vars(args))

    def serial_command(fn):
        """Set up and tear down serial connections."""
        def _decorated(self, args):
            ports = args.get('port', None)
            if ports is None:
                ports = self.find_comport()

            for port in ports:
                sp = serial.Serial(port, timeout=5)
                fn(self, sp, args)
                sp.close()
        return _decorated

    def _get_status(self, serial):
        serial.write(b'32BLINFO\x00')
        response = serial.read(8)
        if response == b'':
            raise RuntimeError('Timeout waiting for 32Blit status.')
        return 'game' if response == b'32BL_EXT' else 'firmware'

    def _reset(self, serial, timeout=5.0):
        serial.write(b'32BL_RST\x00')
        serial.flush()
        serial.close()
        time.sleep(0.5)
        t_start = time.time()
        while time.time() - t_start < timeout:
            try:
                serial.open()
                return
            except SerialException:
                time.sleep(0.1)
        raise RuntimeError(f"Failed to connect to 32Blit on {serial.port} after reset")

    def _reset_to_firmware(self, serial):
        if self._get_status(serial) == 'game':
            self._reset(serial)

    def _send_file(self, serial, file, dest, directory='/'):
        sent_byte_count = 0
        chunk_size = 64
        file_name = file.name
        file_size = file.stat().st_size

        if dest == 'sd':
            if not directory.endswith('/'):
                directory = f'{directory}/'

            logging.info(f'Saving {file} ({file_size} bytes) as {file_name} in {directory}')
            command = f'32BLSAVE{directory}{file_name}\x00{file_size}\x00'
        elif dest == 'flash':
            logging.info(f'Flashing {file} ({file_size} bytes)')
            command = f'32BLPROG{file_name}\x00{file_size}\x00'

        serial.reset_output_buffer()
        serial.write(command.encode('ascii'))

        with open(file, 'rb') as file:
            progress = tqdm(total=file_size, desc="Flashing...", unit_scale=True, unit_divisor=1024, unit="B", ncols=70, dynamic_ncols=True)

            while sent_byte_count < file_size:
                data = file.read(chunk_size)
                serial.write(data)
                serial.flush()
                sent_byte_count += chunk_size
                progress.update(chunk_size)

    @serial_command
    def run_save(self, serial, args):
        self._reset_to_firmware(serial)
        self._send_file(serial, args.get('file'), 'sd', directory=args.get('directory'))

    @serial_command
    def run_flash(self, serial, args):
        self._reset_to_firmware(serial)
        self._send_file(serial, args.get('file'), 'flash')

    @serial_command
    def run_delete(self, serial, args):
        self._reset_to_firmware(serial)
        serial.write(b'32BLERSE\x00')

        offset = args.get('offset')
        if offset is None:
            offset = args.get('block') * 64 * 1024

        serial.write(struct.pack("<I", offset))

    @serial_command
    def run_list(self, serial, args):
        self._reset_to_firmware(serial)

        serial.write(b'32BL__LS\x00')
        offset_str = serial.read(4)

        while offset_str != '' and offset_str != b'\xff\xff\xff\xff':
            offset, = struct.unpack('<I', offset_str)

            size, = struct.unpack('<I', serial.read(4))
            meta_head = serial.read(10)
            meta_size, = struct.unpack('<H', meta_head[8:])

            meta = None
            if meta_size:
                size += meta_size + 10
                try:
                    meta = struct_blit_meta_standalone.parse(meta_head + serial.read(meta_size))
                except ConstructError:
                    pass

            block_size = 64 * 1024

            offset_blocks = offset // block_size
            size_blocks = (size - 1) // block_size + 1

            print(f"""Game at block {offset_blocks}
    Size:        {size_blocks} blocks ({size / 1024:.1f}kB)""")

            if meta is not None:
                print(f"""    Title:       {meta.data.title}
    Description: {meta.data.description}
    Version:     {meta.data.version}
    Author:      {meta.data.author}
""")

            offset_str = serial.read(4)

    @serial_command
    def run_debug(self, serial, args):
        pass

    @serial_command
    def run_reset(self, serial, args):
        logging.info('Resetting your 32Blit...')
        self._reset(serial)

    @serial_command
    def run_info(self, serial, args):
        logging.info('Getting 32Blit run status...')
        status = self._get_status(serial)
        print(f'Running: {status}')
