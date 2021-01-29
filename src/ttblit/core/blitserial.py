import functools
import logging
import pathlib
import struct
import time

import serial.tools.list_ports
from construct.core import ConstructError
from tqdm import tqdm

from ..core.struct import struct_blit_meta_standalone


class BlitSerialException(Exception):
    pass


class BlitSerialWrongModeException(BlitSerialException):
    pass


def firmware_command(fn):
    """Check if we are in the firmware before running commands that require it."""
    @functools.wraps(fn)
    def _decorated(self, *args, **kwargs):
        # if self.status != 'firmware':
        #    # Note: we could instead reset_to_firmware here.
        #    raise BlitSerialWrongModeException("32Blit is not in firmware mode. Please exit game or reset.")
        return fn(self, *args, **kwargs)

    return _decorated


class BlitSerial(serial.Serial):
    def __init__(self, port):
        super().__init__(port, timeout=5)

    @classmethod
    def find_comport(cls):
        ret = []
        for comport in serial.tools.list_ports.comports():
            if comport.vid == 0x0483 and comport.pid == 0x5740:
                logging.info(f'Found 32Blit on {comport.device}')
                ret.append(comport.device)

        if ret:
            return ret

        raise RuntimeError('Unable to find 32Blit')

    @classmethod
    def validate_comport(cls, device):
        if device.lower() == 'auto':
            return cls.find_comport()[:1]
        if device.lower() == 'all':
            return cls.find_comport()

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

    @property
    def status(self):
        self.write(b'32BLINFO\x00')
        response = self.read(8)
        if response == b'':
            raise RuntimeError('Timeout waiting for 32Blit status.')
        return 'game' if response == b'32BL_EXT' else 'firmware'

    def reset(self, timeout=5.0):
        self.write(b'32BL_RST\x00')
        self.flush()
        self.close()
        time.sleep(1.0)
        t_start = time.time()
        while time.time() - t_start < timeout:
            try:
                self.open()
                return
            except BlitSerialException:
                time.sleep(0.1)
        raise RuntimeError(f"Failed to connect to 32Blit on {serial.port} after reset")

    def reset_to_firmware(self, timeout=5.0):
        if self.status != 'firmware':
            self.reset(timeout)

    @firmware_command
    def send_file(self, file, drive, directory=pathlib.PurePosixPath('/')):
        sent_byte_count = 0
        chunk_size = 64
        file_name = file.name
        file_size = file.stat().st_size

        if drive == 'sd':
            logging.info(f'Saving {file} ({file_size} bytes) as {file_name} in {directory}')
            command = f'32BLSAVE{directory}/{file_name}\x00{file_size}\x00'
        elif drive == 'flash':
            logging.info(f'Flashing {file} ({file_size} bytes)')
            command = f'32BLPROG{file_name}\x00{file_size}\x00'
        else:
            raise TypeError(f'Unknown destination {drive}.')

        self.reset_output_buffer()
        self.write(command.encode('ascii'))

        with open(file, 'rb') as file:
            progress = tqdm(total=file_size, desc="Flashing...", unit_scale=True, unit_divisor=1024, unit="B", ncols=70, dynamic_ncols=True)
            while sent_byte_count < file_size:
                data = file.read(chunk_size)
                self.write(data)
                self.flush()
                sent_byte_count += chunk_size
                progress.update(chunk_size)

    @firmware_command
    def erase(self, offset):
        self.write(b'32BLERSE\x00')
        self.write(struct.pack("<I", offset))

    @firmware_command
    def list(self):
        self.write(b'32BL__LS\x00')
        offset_str = self.read(4)

        while offset_str != '' and offset_str != b'\xff\xff\xff\xff':
            offset, = struct.unpack('<I', offset_str)

            size, = struct.unpack('<I', self.read(4))
            meta_head = self.read(10)
            meta_size, = struct.unpack('<H', meta_head[8:])

            meta = None
            if meta_size:
                size += meta_size + 10
                try:
                    meta = struct_blit_meta_standalone.parse(meta_head + self.read(meta_size))
                except ConstructError:
                    pass

            yield (meta, offset, size)

            offset_str = self.read(4)
