import tempfile

import pytest


@pytest.fixture
def test_input_bin(test_resources):
    temp_bin = tempfile.NamedTemporaryFile('r+b', suffix='.bin')
    temp_bin.write(open(test_resources / "doom-fire.bin", "rb").read())
    temp_bin.flush()
    return temp_bin


@pytest.fixture
def test_input_elf(test_resources):
    temp_bin = tempfile.NamedTemporaryFile('r+b', suffix='.bin')
    temp_bin.write(open(test_resources / "doom-fire.elf", "rb").read())
    temp_bin.flush()
    return temp_bin


@pytest.fixture
def test_output_file():
    temp_bin = tempfile.NamedTemporaryFile('r+b', suffix='.blit')
    return temp_bin


def test_relocs(parsers, test_input_bin, test_input_elf, test_output_file):
    from ttblit.tool import relocs

    parser, subparser = parsers

    relocs = relocs.Relocs(subparser)

    args = parser.parse_args([
        'relocs',
        '--bin-file', test_input_bin.name,
        '--elf-file', test_input_elf.name,
        '--output', test_output_file.name])

    relocs.run(args)
