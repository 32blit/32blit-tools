import pathlib

import serial.tools.list_ports
from tqdm import tqdm

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

        self.op_delete = operations.add_parser('delete', help='Delete a game/file from your 32Blit')
        self.op_list = operations.add_parser('list', help='List games/files on your 32Blit')
        self.op_debug = operations.add_parser('debug', help='Enter serial debug mode')
        self.op_reset = operations.add_parser('reset', help='Reset your 32Blit')

    def find_comport(self):
        for comport in serial.tools.list_ports.comports():
            if comport.vid == 0x0483 and comport.pid == 0x5740:
                print(f'Found 32Blit on {comport.device}')
                return comport.device
        raise RuntimeError('Unable to find 32Blit')

    def validate_comport(self, device):
        if device.lower() == 'auto':
            return self.find_comport()
        for comport in serial.tools.list_ports.comports():
            if comport.device == device:
                if comport.vid == 0x0483 and comport.pid == 0x5740:
                    print(f'Found 32Blit on {comport.device}')
                    return device
        raise RuntimeError(f'Unable to find 32Blit on {device}')

    def run(self, args):
        if args.operation is not None:
            dispatch = f'run_{args.operation}'
            getattr(self, dispatch)(vars(args))

    def serial_command(fn):
        """Set up and tear down a serial connection."""
        def _decorated(self, args):
            port = args.get('port', None)
            if port is None:
                port = self.find_comport()
            sp = serial.Serial(port)
            fn(self, sp, args)
            sp.close()
        return _decorated

    def _save(self, serial, file):
        sent_byte_count = 0
        chunk_size = 64
        file_name = file.name
        file_size = file.stat().st_size
        print(f'Saving {file} ({file_size} bytes) as {file_name}')

        command = f'32BLSAVE{file_name}\x00{file_size}\x00'

        serial.reset_output_buffer()
        serial.write(command.encode('ascii'))

        with open(file, 'rb') as file:
            progress = tqdm(total=file_size, desc="Flashing...", unit_scale=True, unit_divisor=1024, unit="B", ncols=70, dynamic_ncols=True)

            while sent_byte_count < file_size:
                data = file.read(chunk_size)
                serial.write(data)
                sent_byte_count += chunk_size
                progress.update(chunk_size)

    @serial_command
    def run_save(self, serial, args):
        self._save(serial, args.get('file'))

    @serial_command
    def run_delete(self, serial, args):
        pass

    @serial_command
    def run_list(self, serial, args):
        pass

    @serial_command
    def run_debug(self, serial, args):
        pass

    @serial_command
    def run_reset(self, serial, args):
        print('Resetting your 32Blit...')
        serial.write(b'32BL_RST\x00')
