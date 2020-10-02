import logging
import pathlib
import time

import serial.tools.list_ports
from serial.serialutil import SerialException
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
        self.op_save.add_argument('--directory', type=str, default='/', help='Target directory')

        self.op_flash = operations.add_parser('flash', help='Flash a game to your 32Blit')
        self.op_flash.add_argument('--file', type=pathlib.Path, required=True, help='File to flash')

        self.op_delete = operations.add_parser('delete', help='Delete a game/file from your 32Blit')
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
        serial.close()
        t_start = time.time()
        while time.time() - t_start < timeout:
            try:
                serial.open()
                break
            except SerialException:
                time.sleep(0.1)

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
        pass

    @serial_command
    def run_list(self, serial, args):
        pass

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
