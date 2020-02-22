#!/usr/bin/env python3

import pathlib

import yaml

import serial.tools.list_ports
from tqdm import tqdm

from ..core.outputformat import CHeader, CSource, RawBinary
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
        if args.port is None:
           args.port = self.find_comport()

        self.serial = serial.Serial(args.port)

        if args.operation is not None:
            dispatch = f'run_{args.operation}'
            getattr(self, dispatch)(args)

        self.serial.close()

    def run_save(self, args):     
        sent_byte_count = 0
        chunk_size = 64
        file_name = args.file.name
        file_size = args.file.stat().st_size
        print(f'Saving {args.file} ({file_size} bytes) as {file_name}')

        command = f'32BLSAVE{file_name}\x00{file_size}\x00'

        self.serial.reset_output_buffer()
        self.serial.write(command.encode('ascii'))

        with open(args.file, 'rb') as file:
            progress = tqdm(total=file_size, desc="Flashing...", unit_scale=True, unit_divisor=1024, unit="B", ncols=70, dynamic_ncols=True)

            while sent_byte_count < file_size:
                data = file.read(chunk_size)
                self.serial.write(data)
                sent_byte_count += chunk_size
                progress.update(chunk_size)

    def run_delete(self, args):
        pass

    def run_list(self, args):
        pass

    def run_debug(self, args):
        pass
  
    def run_reset(self, args):
        print('Resetting your 32Blit...')
        self.serial.write(b'32BL_RST\x00')
