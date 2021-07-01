import os
import pathlib
import tempfile

import pytest


@pytest.fixture
def output_dir():
    temp_output = tempfile.TemporaryDirectory()
    return temp_output


def test_setup_cli(output_dir, test_resources):
    from ttblit import main

    wd = os.getcwd()
    os.chdir(output_dir.name)

    with pytest.raises(SystemExit):
        main([
            'setup',
            '--project-name', 'Test',
            '--author-name', 'Test',
            '--sdk-path', str(test_resources),
            '--git',
            '--vscode',
            '--visualstudio'
        ])

    assert (pathlib.Path(output_dir.name) / "test" / "CMakeLists.txt").exists()

    os.chdir(wd)