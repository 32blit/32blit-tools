import io
import pathlib

import mock
import pytest
from ttblit.core.blitserial import BlitSerial, BlitSerialException


def test_comport():
    """Test serial port discovery."""
    def comports():
        class Comport:
            def __init__(self, vid, pid, device):
                self.vid = vid
                self.pid = pid
                self.device = device

        for c in ((0, 0, "notblit"), (0, 0, "notblit"), (0x0483, 0x5740, "_fakeserial_"), (None, None, "_noidserial_")):
            yield Comport(*c)

    with mock.patch("serial.tools.list_ports.comports", return_value=comports()):
        BlitSerial.validate_comport("auto")

    with mock.patch("serial.tools.list_ports.comports", return_value=comports()):
        BlitSerial.validate_comport("all")

    with mock.patch("serial.tools.list_ports.comports", return_value=comports()):
        BlitSerial.validate_comport("_fakeserial_")

    with mock.patch("serial.tools.list_ports.comports", return_value=comports()):
        BlitSerial.validate_comport("_noidserial_")

    with pytest.raises(RuntimeError):
        # Without the mock, no blit should be connected.
        BlitSerial.validate_comport("auto")

    with pytest.raises(RuntimeError):
        # Without the mock, no blit should be connected.
        BlitSerial.validate_comport("_fakeserial_")


class BlitSerialTester(BlitSerial):
    """Mock wrapper around BlitSerial that uses BytesIO to simulate the hardware port."""
    def __init__(self, output):
        self.__reader = io.BytesIO(output)
        self.__writer = io.BytesIO()

    def read(self, n):
        return self.__reader.read(n)

    def write(self, b):
        return self.__writer.write(b)

    def sent_bytes(self):
        return bytes(self.__writer.getbuffer())

    def open(self):
        raise BlitSerialException()

    @property
    def in_waiting(self):
        return 0

    def flush(self):
        pass

    def reset_output_buffer(self):
        pass

    def close(self):
        pass

    @property
    def port(self):
        return "_fakeserial_"


def test_status():
    b = BlitSerialTester(b"32BL_EXT")

    assert b.status == 'game'
    assert b.sent_bytes() == b'32BLINFO\x00'


def test_reset():
    b = BlitSerialTester(b"")
    with pytest.raises(RuntimeError):
        b.reset()
    assert b.sent_bytes() == b"32BL_RST\x00"


def test_send_file(test_resources):
    f = pathlib.Path(test_resources / "doom-fire.blit")
    f_data = f.read_bytes()

    b = BlitSerialTester(b'32BL__OK\x00\x00')
    b.send_file(f, "flash", auto_launch=True)
    assert b.sent_bytes() == b'32BLPROGdoom-fire.blit\x0026322\x00' + f_data + b'32BLLNCHflash:/0\x00'

    b = BlitSerialTester(b'32BL__OK\x00\x00')
    b.send_file(f, "flash", auto_launch=False)
    assert b.sent_bytes() == b'32BLPROGdoom-fire.blit\x0026322\x00' + f_data

    b = BlitSerialTester(b'32BL__OK\x00\x00')
    b.send_file(f, "sd", auto_launch=True)
    assert b.sent_bytes() == b'32BLSAVE//doom-fire.blit\x0026322\x00' + f_data + b'32BLLNCH//doom-fire.blit\x00'

    b = BlitSerialTester(b'32BL__OK\x00\x00')
    b.send_file(f, "sd", auto_launch=False)
    assert b.sent_bytes() == b'32BLSAVE//doom-fire.blit\x0026322\x00' + f_data

    with pytest.raises(TypeError):
        b = BlitSerialTester(b'32BL__OK\x00\x00')
        b.send_file(f, "no_such_drive")


def test_erase():
    b = BlitSerialTester(b"")
    b.erase(0x12345678)
    assert b.sent_bytes() == b'32BLERSE\x78\x56\x34\x12\x00'


def test_list():
    import struct
    from ttblit.core.struct import struct_blit_meta_standalone
    from ttblit.core.palette import Palette

    palette = Palette()
    palette.get_entry(255, 255, 255, 255)

    # TODO: This should be a fixture or something
    metadata = {
        'checksum': 0x12345678,
        'date': "date",
        'title': "title",
        'description': "description",
        'version': "version",
        'author': "author",
        'category': "category",
        'filetypes': "",
        'url': "",
        'icon': {
            'data': {
                'width': 8,
                'height': 8,
                'palette': palette.tostruct(),
                'pixels': b'\x00' * 8 * 8,
            },
        },
        'splash': {
            'data': {
                'width': 128,
                'height': 96,
                'palette': palette.tostruct(),
                'pixels': b'\x00' * 128 * 96,
            },
        },
    }

    test_meta = struct_blit_meta_standalone.build({'data': metadata})

    fake_offs = 0x50000
    fake_size = 0x15000

    test_data = b''.join([
        struct.pack("<II", fake_offs, fake_size),
        test_meta,
        b"\xff\xff\xff\xff",
    ])

    b = BlitSerialTester(test_data)
    x = list(b.list())
    assert b.sent_bytes() == b'32BL__LS\x00'
    assert len(x) == 1
    meta, offset, size = x[0]
    assert offset == fake_offs
    assert size == fake_size + len(test_meta)
    for k in ['author', 'title', 'description']:
        assert metadata[k] == meta['data'][k]


def test_launch():
    b = BlitSerialTester(b"")
    b.launch("filename_here")
    assert b.sent_bytes() == b'32BLLNCHfilename_here\x00'
