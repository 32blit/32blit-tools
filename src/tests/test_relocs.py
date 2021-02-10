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


def test_relocs(test_input_bin, test_input_elf, test_output_file):
    from ttblit import main

    with pytest.raises(SystemExit):
        main([
            'relocs',
            '--bin-file', test_input_bin.name,
            '--elf-file', test_input_elf.name,
            '--output', test_output_file.name
        ])
