import pytest


def test_version(capsys):
    from ttblit import __version__, main

    with pytest.raises(SystemExit):
        main(['version'])

    assert capsys.readouterr().out == f'{__version__}\n'
